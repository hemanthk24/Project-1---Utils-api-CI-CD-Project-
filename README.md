# Utils API — CI/CD Practice Project
 
A small FastAPI service that exposes simple utility functions (slugify, prime
check, fibonacci, palindrome check, JSON flatten, word frequency) — built not
because the functions are interesting, but as a vehicle to practice the full
DevOps loop:
 
```
write code → unit test → integration test → Dockerize → CI runs tests →
CD builds & pushes image to ECR → EC2 pulls & runs the new container
```
 
---
 
## 1. Project structure
 
```
utils-api/
├── app/
│   ├── main.py              # FastAPI routes — wires HTTP endpoints to utils.py
│   ├── utils.py             # pure functions, no FastAPI/HTTP dependency
│   └── __init__.py
├── tests/
│   ├── test_utils.py        # unit tests — call functions directly
│   └── test_api.py          # integration tests — call functions via HTTP (TestClient)
├── Dockerfile                # multi-stage build → small, non-root production image
├── .dockerignore
├── requirements.txt          # runtime deps only (fastapi, uvicorn, pydantic)
├── requirements-dev.txt      # runtime + test deps (pytest, httpx)
├── pytest.ini                 # tells pytest how to find the `app` package
└── .github/workflows/ci-cd.yml
```
 
---
 
## 2. Running it locally
 
```bash
cd utils-api
pip install -r requirements-dev.txt
pytest -v                      # confirm logic works before running anything
uvicorn app.main:app --reload  # start the dev server
```
 
Visit `http://127.0.0.1:8000/docs` for interactive Swagger UI.
 
---
 
## 3. Why `pytest.ini` exists
 
```ini
[pytest]
pythonpath = .
```
 
Your test files do this:
```python
from app.utils import slugify
```
 
For that import to work, Python needs `app/` to be reachable as a package
from wherever pytest runs. Since `tests/` sits **next to** `app/` (not inside
it), there's no automatic relationship between them — without help, pytest
would fail with:
 
```
ModuleNotFoundError: No module named 'app'
```
 
`pythonpath = .` tells pytest: *"add the folder this ini file lives in (the
project root) to Python's import search path before collecting tests."*
Once the project root is importable, `app.utils` and `app.main` resolve
correctly no matter which subfolder you run `pytest` from.
 
This file also marks the project root as pytest's **rootdir** — the anchor
point pytest uses to consistently discover `test_*.py` files across the
whole project, regardless of your current working directory.
 
**One-line summary:** `pytest.ini` exists solely to make `from app.xxx import`
work inside the test files — nothing more exotic than that for this project.
 
---
 
## 4. What the tests actually do
 
**`tests/test_utils.py` — unit tests.**
Calls functions in `utils.py` directly (`slugify("Hello World!")`) and
asserts the output. No server, no HTTP, no network — just plain Python
function calls. This is where logic bugs get caught, fast (milliseconds).
 
**`tests/test_api.py` — integration tests.**
Uses FastAPI's `TestClient` to simulate real HTTP requests
(`client.post("/string/slugify", json={"text": "..."})`) without actually
starting a live server on a real port. This checks the *wiring* — that
routes exist, request/response shapes are correct, status codes are right.
 
Both run automatically via `pytest -v` — you never call them manually.
Pytest auto-discovers any file matching `test_*.py` and any function inside
it starting with `test_`, then runs each one, reporting PASSED/FAILED per
function based on whether its `assert` statements held true.
 
---
 
## 5. The Dockerfile (multi-stage build)
 
```dockerfile
FROM python:3.11-slim AS builder      # Stage 1: throwaway build environment
...
RUN pip install --no-cache-dir -r requirements.txt
 
FROM python:3.11-slim                   # Stage 2: fresh, clean environment
COPY --from=builder /venv /venv         # only the finished venv is copied over
COPY app ./app
RUN useradd -m appuser
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
 
**Why two stages:** each `FROM` starts a completely separate, empty
filesystem. Stage 1 gets messy — pip cache, `requirements.txt`, potential
build tools — none of which needs to exist in the final image. Stage 2
starts fresh and pulls across *only* the finished `/venv` folder via
`COPY --from=builder`. Everything else from stage 1 is discarded, keeping
the final image small.
 
**Why `useradd -m appuser` + `USER appuser`:** by default, containers run as
root — meaning if an attacker ever finds a way to execute code inside your
running app (e.g. via a library vulnerability), that code inherits **root's
full permissions** inside the container automatically, no extra steps needed
on the attacker's part. Switching to a low-privilege user (`appuser`)
contains the blast radius: a compromised process can only touch what
`appuser` is allowed to touch (its own app files), not system-level
resources. This is purely a container-internal concept — `appuser` has no
relationship to any user on the real EC2 host.
 
---
 
## 6. GitHub Secrets — what they are and why
 
Stored at: repo → **Settings → Secrets and variables → Actions**.
 
| Secret | Purpose |
|---|---|
| `AWS_ACCESS_KEY_ID` | Identifies the IAM user GitHub Actions authenticates as |
| `AWS_SECRET_ACCESS_KEY` | The matching password/credential for that IAM user |
| `EC2_HOST` | Public IP/DNS of your EC2 instance, so SSH knows where to connect |
| `EC2_USER` | SSH login username (`ubuntu` for Ubuntu AMIs) |
| `EC2_SSH_KEY` | The full private key content (from your `.pem` file) used to authenticate the SSH connection |
 
Secrets are encrypted at rest, never shown in logs, and only injected into
the workflow at runtime via `${{ secrets.NAME }}` — this is why credentials
never appear hardcoded in the YAML file itself.
 
---
 
## 7. How the AWS login actually happens (step by step)
 
There are **two separate AWS logins** in this pipeline — one on GitHub's
runner, one on your EC2 box. They're easy to conflate, so here's the exact
sequence:
 
### Login #1 — GitHub Actions runner authenticates to AWS
 
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ env.AWS_REGION }}
```
This action takes your IAM user's access key/secret and configures the AWS
CLI on the (temporary, disposable) GitHub-hosted VM — as if you'd run
`aws configure` manually. From this point on, any `aws` command run in later
steps on this VM is authenticated as your IAM user.
 
```yaml
- uses: aws-actions/amazon-ecr-login@v2
  id: login-ecr
```
This action uses that now-configured AWS CLI identity to request a
temporary ECR password, then runs `docker login` against your ECR registry
under the hood. It also outputs the full registry URL
(`steps.login-ecr.outputs.registry`) so later steps don't need to hardcode
your AWS account ID.
 
At this point, `docker push` from the GitHub runner is authorized.
 
### Login #2 — EC2 instance authenticates to AWS (separately)
 
The GitHub runner's login has **no bearing on EC2** — EC2 is a completely
different machine and needs its own, independent authentication. This
happens inside the SSH deploy step's `script:` block, which runs commands
*on the EC2 box itself*:
 
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_REGISTRY
```
 
For this to succeed, the EC2 instance itself needs AWS credentials
available to it. This is where the **IAM role** comes in (see below) —
instead of manually configuring access keys on the server, an IAM role
attached to the instance lets the AWS CLI silently fetch temporary
credentials from EC2's built-in instance metadata service. `aws ecr
get-login-password` uses whatever identity is available — the attached
role — with zero credentials ever stored on disk on the server.
 
**Summary of the two logins:**
| Where | Login method | Why |
|---|---|---|
| GitHub Actions runner | Access key + secret (from GitHub Secrets) | To push the newly built image to ECR |
| EC2 instance | IAM role attached to the instance | To pull the image down from ECR |
 
---
 
## 8. Why an IAM role for EC2 (instead of access keys)
 
You *could* run `aws configure` on the EC2 box with a raw access
key/secret — but that means a real, long-lived AWS credential sits in a
file on disk on a server that's reachable from the internet. If that server
is ever compromised, the attacker walks away with a working AWS credential.
 
An **IAM role attached to the instance** avoids this entirely:
- No credentials are ever stored anywhere on the EC2 filesystem.
- AWS automatically rotates short-lived, temporary credentials behind the
  scenes via the instance metadata service.
- The role can be scoped to the *minimum* permission needed — in this case,
  `AmazonEC2ContainerRegistryReadOnly` — so even in a worst-case compromise,
  the blast radius is limited to "can pull images from ECR," nothing more
  (can't push, can't touch other AWS services, can't modify infrastructure).
Setup path: **IAM → Roles → Create role → Trusted entity: AWS service →
Use case: EC2 → attach `AmazonEC2ContainerRegistryReadOnly` → name it →
create.** Then: **EC2 → your instance → Actions → Security → Modify IAM
role → select the new role.** No reboot needed — it applies immediately.
 
---
 
## 9. ECR naming — registry vs. repository
 
- **Registry**: one per AWS account per region, auto-named
  (`<account-id>.dkr.ecr.<region>.amazonaws.com`) — you never choose this,
  the `amazon-ecr-login` action resolves it for you.
- **Repository**: a named "shelf" inside that registry holding all versions
  of one app's images — **you name this yourself** (`utils-api` in this
  project), and it must exactly match `ECR_REPOSITORY` in the workflow's
  `env:` block. It does **not** need to match your GitHub repo name or your
  local folder name — those are entirely independent.
---
 
## 10. The full pipeline, end to end
 
```
git push origin main
    │
    ▼
[test job]        checkout → install deps → pytest -v
    │  (only proceeds if this job succeeds)
    ▼
[build-and-deploy job]   (only runs on push to main, not on PRs)
    │
    ├─ configure-aws-credentials   (GitHub runner logs into AWS)
    ├─ amazon-ecr-login             (GitHub runner logs into ECR, outputs registry URL)
    ├─ docker build/tag/push        (image pushed to ECR, tagged with commit SHA + "latest")
    │
    └─ SSH into EC2:
         ├─ aws ecr get-login-password → docker login   (EC2 logs into ECR via its IAM role)
         ├─ docker pull ...:latest
         ├─ docker stop/rm utils-api  (|| true — safe no-op on first deploy)
         └─ docker run -d --name utils-api -p 8000:8000 ...:latest
```
 
---
 
## 11. One-time manual setup checklist (not automated by the pipeline)
 
- [ ] Launch EC2 instance (Ubuntu), open inbound ports 22 and 8000 in its
      Security Group
- [ ] Install Docker + AWS CLI on the instance (`sudo apt install docker.io awscli`)
- [ ] Add `ubuntu` user to the `docker` group, re-login
- [ ] Create IAM role with `AmazonEC2ContainerRegistryReadOnly`, attach to
      the instance
- [ ] Create ECR repository named `utils-api`
- [ ] Create an IAM user for GitHub Actions with ECR push permissions,
      generate access keys
- [ ] Add all 5 GitHub Secrets
Everything after this checklist is fully automated by `ci-cd.yml` on every
push to `main`.
