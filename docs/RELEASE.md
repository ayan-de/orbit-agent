# Orbit Agent - Release Guide

## Prebuilt Releases

Orbit Agent provides prebuilt releases for fast installation (~5 seconds vs 2-5 minutes from source).

### Supported Platforms

- **Linux**: x64, arm64
- **macOS**: x64, arm64 (Apple Silicon)
- **Windows**: WSL (Windows Subsystem for Linux)

### Release Artifacts

Each release includes:

- `orbit-agent-{version}-{platform}-{arch}.tar.gz` - Complete prebuilt package
- `orbit-agent-{version}-{platform}-{arch}.tar.gz.sha256` - Checksum for verification

### Contents

Each prebuilt release contains:

- Python Agent (FastAPI + LangGraph)
- NestJS Bridge (Command execution service)
- SvelteKit Frontend (Web UI)
- Desktop TUI (Terminal interface)
- Installation scripts
- Configuration files
- Documentation

## Building Prebuilt Releases

### Manual Build

To build a prebuilt release locally:

```bash
# Build for current platform
./scripts/build_release.sh --version 1.0.0

# Build for specific platform
./scripts/build_release.sh --version 1.0.0 --platform linux --arch x64

# Build with custom output directory
./scripts/build_release.sh --version 1.0.0 --output ./custom-releases
```

The release will be created in the `./releases/` directory.

### CI/CD Build

Automated builds are triggered by:

1. **Push to main**: Creates development builds with version format `YYYYMMDD-commit-hash`
2. **Version tags (v*)**: Creates official releases
3. **Manual trigger**: Via GitHub Actions UI

## Creating a Release

### 1. Tag the Release

```bash
# Tag the current commit
git tag -a v1.0.0 -m "Release v1.0.0"

# Push the tag
git push origin v1.0.0
```

### 2. CI/CD Process

1. GitHub Actions detects the tag
2. Builds releases for all supported platforms
3. Runs tests on the built artifacts
4. Creates GitHub release with artifacts
5. Generates release notes

### 3. Verification

After the workflow completes:

1. Download the release from GitHub Releases
2. Verify the checksum:
   ```bash
   sha256sum -c orbit-agent-1.0.0-linux-x64.tar.gz.sha256
   ```
3. Test installation:
   ```bash
   tar -xzf orbit-agent-1.0.0-linux-x64.tar.gz
   cd orbit-agent-1.0.0-linux-x64
   ./install.sh
   ```

## Installation

### Quick Install (Prebuilt)

```bash
curl -fsSL https://ayande.xyz/install.sh | bash
```

### Manual Install (Prebuilt)

```bash
# Download
wget https://github.com/ayan-de/orbit-agent/releases/download/v1.0.0/orbit-agent-1.0.0-linux-x64.tar.gz

# Verify checksum
sha256sum -c orbit-agent-1.0.0-linux-x64.tar.gz.sha256

# Extract
tar -xzf orbit-agent-1.0.0-linux-x64.tar.gz

# Install
cd orbit-agent-1.0.0-linux-x64
./install.sh
```

### Source Install (Fallback)

```bash
# Force source installation
curl -fsSL https://ayande.xyz/install.sh | bash -s -- --no-prebuilt
```

## Release Versioning

### Version Format

- **Official releases**: `v{major}.{minor}.{patch}` (e.g., `v1.0.0`)
- **Pre-releases**: `v{major}.{minor}.{patch}-{pre}` (e.g., `v1.0.0-alpha`)
- **Development builds**: `YYYYMMDD-{commit-hash}` (e.g., `20240308-abc1234`)

### Semantic Versioning

- **Major (X.0.0)**: Breaking changes
- **Minor (1.X.0)**: New features, backward compatible
- **Patch (1.0.X)**: Bug fixes, backward compatible

### Pre-release Tags

- `alpha`: Early development, may be unstable
- `beta`: Feature complete, testing needed
- `rc`: Release candidate, ready for production

## Troubleshooting

### Build Failures

If the build fails:

1. Check the workflow logs on GitHub Actions
2. Ensure all dependencies are specified in requirements.txt
3. Verify Node.js and Python versions
4. Check for build errors in the platform-specific builds

### Checksum Mismatch

If checksum verification fails:

1. Re-download the release
2. Verify you downloaded the correct version
3. Check for network corruption
4. Report the issue on GitHub

### Installation Issues

If installation fails:

1. Ensure you have sufficient disk space
2. Check Python 3.10+ and Node.js are installed
3. Verify you have write permissions for `~/.orbit`
4. Try source installation as a fallback

## Security

### Checksum Verification

Always verify checksums before installation:

```bash
sha256sum -c orbit-agent-{version}-{platform}-{arch}.tar.gz.sha256
```

### GPG Signing (Future)

Future releases may include GPG signatures:

```bash
gpg --verify orbit-agent-{version}-{platform}-{arch}.tar.gz.asc
```

## Automation

### Build Script

The `scripts/build_release.sh` script automates:

- Platform detection
- Python environment setup
- Node.js component building
- Archive creation
- Checksum generation

### CI/CD

The `.github/workflows/build-release.yml` workflow provides:

- Matrix builds for multiple platforms
- Automated testing
- GitHub release creation
- Artifact hosting

## Maintenance

### Updating Build Script

To update the build process:

1. Modify `scripts/build_release.sh`
2. Test locally for each platform
3. Commit and push changes
4. Verify CI/CD builds succeed

### Adding New Platforms

To add support for a new platform:

1. Update `scripts/build_release.sh` with platform detection
2. Add platform to matrix in `.github/workflows/build-release.yml`
3. Test the build process
4. Verify installation works on the new platform

## Support

For issues with releases:

- GitHub Issues: https://github.com/ayan-de/orbit-agent/issues
- Documentation: https://github.com/ayan-de/orbit-agent/blob/main/docs/
- Installation Guide: https://github.com/ayan-de/orbit-agent/blob/main/docs/INSTALLATION.md
