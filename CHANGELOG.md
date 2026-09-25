# Changelog

## [1.1.1] - Stability Patch

### Fixed
- Stabilized Windows WMI adapter detection for virtual networks.
- Ensured future-proof semantic versioning for the auto-updater pipeline.


## [1.1.0] - 2026-09-21

### Added
- **Live ISP Dashboard:** Real-time extraction of Active Network Adapters, Local IPv4, Default Gateways, and Retail Provider names.
- **Privacy Controls:** Added a UI toggle to hide/show the Public IP address for safe screen sharing.
- **Multi-line Console:** Upgraded the execution console to a scrollable, multi-line format with timestamp tracking and clipboard copy support.

### Changed
- **Parallel Speed Tests:** Engineered a dynamic cache isolation system allowing BDIX and RAW speed tests to execute in perfect, simultaneous parallel without crashing.
- **Smart Retry Engine:** The RAW speed test now dynamically cycles through top Singapore servers (Singtel, Campana, Pacific Internet, CBN) to bypass offline nodes automatically.

### Fixed
- Fixed a deep Windows PowerShell bug that caused Local IPv4 addresses to truncate to a single character.
- Fixed a routing bug where data center upstream names were displayed instead of the actual retail ISP name.


## [1.0.0] - Initial Release

### Added
- Modern, terminal-free graphical dashboard built with HTML, CSS, and JS.
- Automated Python backend with silent command execution.
- DNS profile switcher (Cache: 10.11.12.13, Raw: 1.1.1.1, DHCP Auto) with visual feedback.
- Deep network TCP/IP stack and Winsock repair module.
- Integrated ping telemetry covering Quad9, Cloudflare, Google DNS, ISP Cache, and Singapore Game Clusters.
- Automated Ookla Speedtest diagnostics for BDIX and International (RAW) routing.
- Infinite split-history tracking for both Ping and Speed tests, saved locally.
- Professional GitHub auto-updater engine.
