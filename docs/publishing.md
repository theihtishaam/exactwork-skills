# Publish your copy on GitHub

The release folder is ready to become a repository. No GitHub repository or release was created automatically.

1. Create an empty repository named `exactwork-skills` or a name you prefer. The repository name may change without changing the skill names.
2. Upload the **contents** of this folder so `README.md`, `skills/`, `tools/`, and `LICENSE` are at the repository root. Include `.github/workflows/check.yml`, `.gitignore`, and `.gitattributes`; some file pickers hide dotfiles.
3. Keep the MIT notice and image provenance. Review the research and evaluation limits before changing performance claims.
4. Let GitHub Actions run. A local Windows test pass is not a completed Linux or remote CI run. Inspect all four matrix combinations before describing them as passing.
5. Tag the tested release `v0.2.0` if desired. Add a repository description such as: “Portable agent skills for focused work, traceable context, and evidence-checked project learning.”

If you prefer Git, initialize and commit locally from this folder, then use GitHub's own displayed commands to connect your new repository. Authenticate through your normal GitHub application flow. This package does not request or store credentials.

The README uses relative asset links, so its images continue to work after upload. There are no fake stars, testimonials, benchmark badges, or owner-specific URLs to replace. Repository visibility, ownership, and publication remain your choice.

Keep `.gitattributes`: hashed skill and evaluation files are marked `-text` so Git does not normalize their line endings and invalidate recorded hashes. The included `.gitignore` keeps local `.exactwork/` learning records out of this repository by default; it does not alter another project's ignore rules.
