# Deployment-Project-VitalAI

This is the Repository for our Software Deployment project.

## Branch Strategy

| Branch    | Purpose                                      |
|-----------|----------------------------------------------|
| `main`    | Production-ready code. Branch protected.     |
| `develop` | Integration branch for feature work.         |
| `hotfix`  | Emergency fixes applied directly from main.  |

## Branch Protection (main)

- Requires **1 approving PR review** before merging
- Requires **CI to pass** before merging
- **Direct pushes blocked**

## Project Board

The project board uses the following workflow columns:

**To Do → In Progress → In Review → Done**

## Contributing

All changes to `main` must go through a Pull Request from a feature branch (e.g. `feature/your-feature`).
Feature branches should be based off `develop`.
