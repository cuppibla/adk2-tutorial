# 🎓 WORKSHOP ONLY — run this INSTEAD of the AI Studio key cell below.
# Prereq: claim your credit first, using the SAME Google account you sign in with here.
import os, subprocess, sys, time

PROJECT_ID = ""            # leave blank to create one automatically
LOCATION   = "us-central1"
MODEL      = "gemini-2.5-flash"   # gemini-flash-latest is an AI-Studio-only alias

from google.colab import auth
auth.authenticate_user()                          # also authenticates the gcloud CLI
acct = subprocess.run(["gcloud", "auth", "list", "--filter=status:ACTIVE",
                       "--format=value(account)"],
                      capture_output=True, text=True).stdout.strip()
print(f"Signed in as: {acct}\n", flush=True)   # flush: Colab's stdout is not a tty,
                                               # so unflushed prints land AFTER subprocess output

if not PROJECT_ID:
    REPO = "/content/adk2-tutorial"
    if not os.path.isdir(REPO):
        subprocess.run(["git", "clone", "-q",
                        "https://github.com/cuppibla/adk2-tutorial.git", REPO], check=True)
    # Finds your GDP credit, creates adk-2-tutorial-XXXX, links it, writes ~/project_id.txt
    rc = subprocess.run([sys.executable, f"{REPO}/scripts/billing_enablement.py"]).returncode
    pid_file = os.path.expanduser("~/project_id.txt")
    if rc != 0 or not os.path.exists(pid_file):
        raise SystemExit(
            f"\n✋ Couldn't create the project automatically.\n"
            f"   Most likely the credit isn't claimed yet, or it was claimed on an\n"
            f"   account other than {acct}.\n"
            f"   → Claim it, wait ~30s, then re-run this cell.\n"
            f"   → Still stuck? Open https://shell.cloud.google.com and run:\n"
            f"        git clone https://github.com/cuppibla/adk2-tutorial.git\n"
            f"        cd adk2-tutorial && ./setup_billing.sh\n"
            f"     then paste the project ID into PROJECT_ID above and re-run this cell."
        )
    PROJECT_ID = open(pid_file).read().strip()

subprocess.run(["gcloud", "config", "set", "project", PROJECT_ID, "--quiet"], check=True)
subprocess.run(["gcloud", "services", "enable",
                "aiplatform.googleapis.com", "--quiet"], check=True)

# Point ADK at Vertex AI instead of AI Studio.
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["GOOGLE_CLOUD_PROJECT"]      = PROJECT_ID
os.environ["GOOGLE_CLOUD_LOCATION"]     = LOCATION
os.environ["ADK_MODEL"]                 = MODEL
os.environ.pop("GOOGLE_API_KEY", None)                         # make sure no stale key wins
os.environ.pop("GEMINI_API_KEY", None)

# A brand-new project is NOT ready the moment gcloud returns. Both the API
# enablement and your owner IAM binding keep propagating for a minute or two,
# and a call inside that window fails with
#     403 Permission 'aiplatform.endpoints.predict' denied ... (or it may not exist)
# which reads like a broken setup and isn't. So prove the path works HERE,
# retrying, instead of letting the first level hit it.
from google import genai

WARMING = ("PERMISSION_DENIED", "SERVICE_DISABLED", "has not been used", "404")
probe = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
for attempt in range(1, 13):                      # up to ~2 min
    try:
        probe.models.generate_content(model=MODEL, contents="ping")
        break
    except Exception as e:
        warming = any(s in str(e) for s in WARMING)
        if attempt == 12 or not warming:
            hint = (f"   → Give it another minute and re-run this cell; new projects are\n"
                    f"     slow to wake. If it still fails, check billing is linked:\n"
                    f"        gcloud billing projects describe {PROJECT_ID}"
                    if warming else
                    "   → This isn't the usual propagation delay — read the error above.")
            raise SystemExit(
                f"\n✋ Vertex AI won't answer on {PROJECT_ID}.\n"
                f"   {type(e).__name__}: {str(e)[:300]}\n{hint}"
            )
        print(f"   waiting for Vertex AI to come up on the new project… ({attempt * 10}s)",
              flush=True)
        time.sleep(10)

print(f"\n✅ Vertex AI on {PROJECT_ID} · {LOCATION} · {MODEL} — answered a test call", flush=True)
