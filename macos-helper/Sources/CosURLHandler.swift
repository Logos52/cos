// CosURLHandler.swift
// Small, high-quality, delightful native macOS helper for the custom `cos://` URL scheme.
// Part of the cos personal OS (https://github.com/.../cos).
//
// - Registers for cos:// via accompanying Info.plist (CFBundleURLTypes).
// - Only runs on-demand when a cos:// URL is opened by the system (LaunchServices).
// - No background agents, no persistent processes, no Dock icon (accessory policy).
// - Parses URLs (cos://brief, cos://research?ticker=NVDA, cos://task-add?text=..., etc.)
//   and maps them *exactly* to `cos` CLI subcommands per the dashboard PRD.
// - Smart Ghostty integration (recommended terminal):
//   - Detects if Ghostty is installed and/or running.
//   - Reuses frontmost window by opening a *new tab* when possible.
//   - Falls back to new window if Ghostty not running.
//   - Uses native AppleScript (Ghostty 1.3+ dictionary) + `input text` for reliable
//     automatic command execution in the new surface, then drops to interactive shell.
// - Graceful fallbacks: Terminal.app (with its classic `do script`), user notifications.
// - Security: strict whitelist of actions only. No arbitrary command execution.
// - Production touches: temp script cleanup, detailed NSLog (view in Console.app),
//   calm actionable notifications, direct CLI test mode, immediate self-termination.
//
// Build: see build.sh or Makefile in this directory.
// Install / one-time setup: `cos setup-macos-handler` (updates the Python CLI entrypoint).
//
// References:
// - PRD: prds/PRD-cos-dashboard-basecamp.md (macOS Custom URL Scheme Handler section)
// - COS_DESIGN_DIRECTION.md (calm, humane, Basecamp-inspired tone in UX and messaging)
// - Ghostty AppleScript: https://ghostty.org/docs/features/applescript

import Foundation
import Cocoa

// MARK: - Constants & Metadata

private let appName = "CosURLHandler"
private let version = "1.0.0"
private let bundleID = "com.wedge.cos-url-handler"

// MARK: - Whitelisted Actions (Security Invariant)

/// All supported cos:// hosts/actions. Only these are ever mapped to CLI commands.
/// This is the single source of truth for the handler's contract with the dashboard.
private enum CosAction: String, CaseIterable {
    case brief
    case capture
    case dashboard
    case vaultScan = "vault-scan"
    case research
    case taskAdd = "task-add"
    case task

    /// The base `cos` subcommand string (without args).
    var cliBase: String {
        switch self {
        case .brief:        return "cos brief"
        case .capture:      return "cos capture"
        case .dashboard:    return "cos dashboard"
        case .vaultScan:    return "cos vault-scan"
        case .research:     return "cos research"
        case .taskAdd, .task: return "cos task add"
        }
    }
}

// MARK: - URL Parsing & Command Mapping

/// Parses a cos:// URL and returns the exact shell command string to execute (or nil on invalid).
/// Examples:
///   cos://brief                     -> "cos brief"
///   cos://research?ticker=NVDA      -> "cos research NVDA"
///   cos://research?software=Textual -> "cos research Textual"
///   cos://task-add?text=Buy+milk    -> "cos task add 'Buy milk'"
///   cos://vault-scan                -> "cos vault-scan"
///
/// Security: Only whitelisted hosts + known query param names are accepted.
/// User-supplied values are shell-quoted for safe execution inside the target terminal.
private func parseAndMapURL(_ url: URL) -> String? {
    guard url.scheme?.lowercased() == "cos" else { return nil }

    guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
          let host = components.host?.lowercased(), !host.isEmpty else {
        return nil
    }

    // Resolve action (support minor variants like "vaultscan")
    let action: CosAction
    if let direct = CosAction(rawValue: host) {
        action = direct
    } else if host == "vaultscan" {
        action = .vaultScan
    } else {
        return nil
    }

    var command = action.cliBase

    // Handle query parameters for parameterized actions
    if let queryItems = components.queryItems, !queryItems.isEmpty {
        switch action {
        case .research:
            // Accept common aliases used in dashboard buttons / generator
            let paramNames = ["ticker", "software", "q", "query"]
            if let value = queryItems.first(where: { paramNames.contains($0.name.lowercased()) })?.value,
               !value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                let clean = value.trimmingCharacters(in: .whitespacesAndNewlines)
                command += " \(shellQuote(clean))"
            }

        case .taskAdd, .task:
            let paramNames = ["text", "title", "description", "add"]
            if let value = queryItems.first(where: { paramNames.contains($0.name.lowercased()) })?.value,
               !value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                let clean = value.trimmingCharacters(in: .whitespacesAndNewlines)
                command += " \(shellQuote(clean))"
            }

        default:
            break
        }
    }

    return command
}

/// Shell-quotes a string for safe inclusion as an argument to the `cos` command
/// when it will be executed by the user's interactive shell (zsh/bash) inside Ghostty/Terminal.
/// Uses single quotes + classic '\'' escape for embedded single quotes.
private func shellQuote(_ s: String) -> String {
    // Fast path: no special chars needed
    if s.rangeOfCharacter(from: CharacterSet(charactersIn: "'\"\\$` \t\n|&;<>()[]{}*?~")) == nil {
        return s
    }
    let escaped = s.replacingOccurrences(of: "'", with: "'\\''")
    return "'\(escaped)'"
}

// MARK: - AppleScript Execution Helper (secure temp script + cleanup)

private struct AppleScriptResult {
    let success: Bool
    let output: String
    let error: String
}

/// Runs the provided AppleScript source by writing it to a unique temp .scpt file,
/// invoking /usr/bin/osascript, capturing stdout/stderr, and cleaning up.
/// This approach supports arbitrary-length scripts without shell escaping nightmares.
private func runAppleScript(_ source: String) -> AppleScriptResult {
    let tempDir = FileManager.default.temporaryDirectory
    let tempURL = tempDir.appendingPathComponent("cos-handler-\(UUID().uuidString).scpt")

    do {
        try source.write(to: tempURL, atomically: true, encoding: .utf8)

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        process.arguments = [tempURL.path]

        let stdout = Pipe()
        let stderr = Pipe()
        process.standardOutput = stdout
        process.standardError = stderr

        try process.run()
        process.waitUntilExit()

        let outData = stdout.fileHandleForReading.readDataToEndOfFile()
        let errData = stderr.fileHandleForReading.readDataToEndOfFile()

        let output = String(data: outData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let error  = String(data: errData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""

        // Always clean up (even on failure)
        try? FileManager.default.removeItem(at: tempURL)

        return AppleScriptResult(
            success: process.terminationStatus == 0,
            output: output,
            error: error
        )
    } catch {
        // Best-effort cleanup
        try? FileManager.default.removeItem(at: tempURL)
        return AppleScriptResult(success: false, output: "", error: "Failed to execute AppleScript: \(error.localizedDescription)")
    }
}

// MARK: - App Detection & Running State

private func isAppInstalled(bundleIdentifier: String) -> Bool {
    NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleIdentifier) != nil
}

private func isAppRunning(name: String) -> Bool {
    // Use System Events for reliable "is running" check (no AppleScript activation side-effects)
    let script = """
    tell application "System Events"
        (name of processes) contains "\(name)"
    end tell
    """
    let result = runAppleScript(script)
    return result.success && result.output.lowercased() == "true"
}

// MARK: - Ghostty Integration (Smart Reuse + Auto Command)

/// Primary integration path. Uses Ghostty's native AppleScript dictionary (1.3+).
/// - Reuses front window + new tab when Ghostty is already running (preferred).
/// - Creates a new window when Ghostty is not running.
/// - Sends the `cos ...` command as keystrokes via `input text` (reliable, no quoting issues
///   inside the surface's shell). The surface starts with the user's normal default shell.
private func runInGhostty(command: String) -> Bool {
    guard isAppInstalled(bundleIdentifier: "com.mitchellh.ghostty") else {
        return false
    }

    let ghosttyIsRunning = isAppRunning(name: "Ghostty")

    // Escape for AppleScript double-quoted string literal ("...\(escaped)...")
    let asSafe = command
        .replacingOccurrences(of: "\\", with: "\\\\")
        .replacingOccurrences(of: "\"", with: "\\\"")

    let creation: String
    if ghosttyIsRunning {
        // Reuse existing (front) window by opening a new tab — exactly as PRD requests.
        creation = "set newTab to new tab in (front window) with configuration cfg"
    } else {
        creation = """
        set newWin to new window with configuration cfg
        set newTab to selected tab of newWin
        """
    }

    let script = """
    tell application "Ghostty"
        activate
        set cfg to new surface configuration
        -- Default shell (user's zsh/fish/etc.) is used when `command` is not set.
        -- We send the cos command as initial input text for reliable execution.
        \(creation)
        set newTerm to focused terminal of newTab
        input text "\(asSafe)\\n" to newTerm
        focus newTerm
    end tell
    """

    let result = runAppleScript(script)
    if result.success {
        NSLog("[\(appName)] Dispatched to Ghostty (running=\(ghosttyIsRunning)): \(command)")
        return true
    } else {
        NSLog("[\(appName)] Ghostty AppleScript failed: \(result.error)")
        // Last-ditch: just launch Ghostty (user will see a fresh window; can manually run cmd)
        return launchGhosttyBare()
    }
}

private func launchGhosttyBare() -> Bool {
    guard let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: "com.mitchellh.ghostty") else {
        return false
    }
    do {
        try NSWorkspace.shared.openApplication(at: url, configuration: NSWorkspace.OpenConfiguration())
        return true
    } catch {
        NSLog("[\(appName)] Failed bare launch of Ghostty: \(error)")
        return false
    }
}

// MARK: - Terminal.app Fallback (Classic, reliable)

private func runInTerminalApp(command: String) -> Bool {
    guard isAppInstalled(bundleIdentifier: "com.apple.Terminal") else {
        return false
    }

    let asSafe = command
        .replacingOccurrences(of: "\\", with: "\\\\")
        .replacingOccurrences(of: "\"", with: "\\\"")

    let script = """
    tell application "Terminal"
        activate
        if (count of windows) > 0 then
            do script "\(asSafe)" in front window
        else
            do script "\(asSafe)"
        end if
    end tell
    """

    let result = runAppleScript(script)
    if result.success {
        NSLog("[\(appName)] Dispatched to Terminal.app: \(command)")
        return true
    } else {
        NSLog("[\(appName)] Terminal AppleScript failed: \(result.error)")
        return false
    }
}

// MARK: - High-Level Dispatch + Fallbacks

private func executeCommandInPreferredTerminal(_ command: String) -> Bool {
    // Preferred: Ghostty (per PRD + COS_DESIGN_DIRECTION)
    if runInGhostty(command: command) {
        return true
    }

    // Graceful fallback: Terminal (built-in, always present on macOS)
    if runInTerminalApp(command: command) {
        return true
    }

    // Ultimate fallback: notify user (no terminal emulator found or all paths failed)
    let msg = "No Ghostty or Terminal available to run: \(command). Install Ghostty (recommended) or check Console.app logs."
    showUserNotification(title: "cos:// Handler", message: msg)
    return false
}

// MARK: - Calm User Feedback (no windows, no Dock icon)

private func showUserNotification(title: String, message: String) {
    // Uses AppleScript `display notification` — works for background/accessory apps,
    // requires no extra entitlements, and matches the calm tone of the project.
    let safeTitle = title.replacingOccurrences(of: "\"", with: "\\\"")
    let safeMsg   = message.replacingOccurrences(of: "\"", with: "\\\"")
    let script = "display notification \"\(safeMsg)\" with title \"\(safeTitle)\""
    _ = runAppleScript(script)
}

// For manual launches of the .app (rare), a blocking dialog is acceptable.
private func showBlockingAlert(title: String, message: String) {
    let safeTitle = title.replacingOccurrences(of: "\"", with: "\\\"")
    let safeMsg   = message.replacingOccurrences(of: "\"", with: "\\\"")
    let script = "display dialog \"\(safeMsg)\" with title \"\(safeTitle)\" buttons {\"OK\"} default button \"OK\""
    _ = runAppleScript(script)
}

// MARK: - Core Handler

private func handleCosURL(_ url: URL) {
    NSLog("[\(appName)] Received URL: \(url.absoluteString)")

    guard let command = parseAndMapURL(url) else {
        let msg = "Unsupported cos:// URL: \(url.absoluteString). Supported hosts: brief, capture, dashboard, vault-scan, research, task-add/task (with appropriate query params)."
        NSLog("[\(appName)] \(msg)")
        showUserNotification(title: "cos:// Handler", message: "Unsupported URL. Open Console.app for details.")
        return
    }

    NSLog("[\(appName)] Mapped to: \(command)")

    let ok = executeCommandInPreferredTerminal(command)
    if !ok {
        // Already notified inside execute path
        NSLog("[\(appName)] All terminal dispatch paths failed for command: \(command)")
    }
}

// MARK: - Application Entry Point

@main
struct CosURLHandler {
    static func main() {
        let args = CommandLine.arguments.dropFirst().map { String($0) }

        // CLI test / introspection mode (very useful during development & `cos setup`)
        if !args.isEmpty {
            let arg = args[0]
            switch arg {
            case "--help", "-h":
                print("""
                \(appName) \(version)
                Native macOS handler for the cos:// custom URL scheme.

                Normal operation: the system launches this app (via the .app bundle)
                when any cos:// URL is opened (e.g. from the cos dashboard HTML).

                Direct testing:
                  \(appName) "cos://brief"
                  \(appName) "cos://research?ticker=NVDA"
                  \(appName) "cos://task-add?text=Buy%20milk"

                Other:
                  \(appName) --version
                  \(appName) --help

                One-time setup (recommended):
                  cos setup-macos-handler

                Full documentation: macos-helper/README.md inside the cos repository.
                """)
                exit(0)

            case "--version":
                print("\(appName) \(version)")
                exit(0)

            default:
                if let url = URL(string: arg), url.scheme?.lowercased() == "cos" {
                    handleCosURL(url)
                    exit(0)
                }
                fputs("Error: Unknown argument. Pass a cos:// URL or use --help.\n", stderr)
                exit(1)
            }
        }

        // URL scheme handler launch path (the normal case)
        let app = NSApplication.shared
        let delegate = HandlerDelegate()
        app.delegate = delegate
        app.setActivationPolicy(.accessory)   // No Dock icon, no menu bar, invisible.

        // If the user double-clicked the .app directly (no URL), be friendly and exit quickly.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
            if !delegate.handledAnyURL {
                showUserNotification(
                    title: "cos:// Handler",
                    message: "Ready. Trigger actions from the cos dashboard (or cos:// links). Ghostty recommended."
                )
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) {
                    app.terminate(nil)
                }
            }
        }

        app.run()
    }
}

private final class HandlerDelegate: NSObject, NSApplicationDelegate {
    var handledAnyURL = false

    func application(_ application: NSApplication, open urls: [URL]) {
        handledAnyURL = true
        for url in urls {
            handleCosURL(url)
        }
        // Quit promptly after work is done — the entire point of the design.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            application.terminate(nil)
        }
    }

    func applicationDidFinishLaunching(_ aNotification: Notification) {
        // Modern URL delivery uses the open(urls:) path above.
        // This is here for completeness / older macOS event paths.
    }
}
