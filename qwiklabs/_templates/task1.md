<!-- Task 1 preserved from Christina Lin's migration (CloudVLab bb0a8bb), -->
<!-- + one line: export ADK_MODEL=gemini-2.5-flash (the AI-Studio alias 404s on Vertex). -->

## Task 1. Prepare your environment

In this task, you clone the tutorial repository, set up a Python virtual environment, install the required libraries, and configure environment variables.

### Activate Cloud Shell

1. On the Google Cloud Console title bar, click **Activate Cloud Shell**.
2. Click **Continue** if prompted.

### Enable the Vertex AI API

1. In Cloud Shell, run the following command to enable the Vertex AI API:

<ql-code-block language="bash">
gcloud services enable aiplatform.googleapis.com
</ql-code-block>

### Clone the tutorial repository

1. In Cloud Shell, run the following command to clone the tutorial repository:

<ql-code-block language="bash">
git clone https://github.com/cuppibla/adk2-tutorial.git
</ql-code-block>

2. Navigate to the repository directory:

<ql-code-block language="bash">
cd adk2-tutorial
</ql-code-block>

### Configure the environment

1. Create a Python virtual environment:

<ql-code-block language="bash">
python3 -m venv venv
</ql-code-block>

2. Activate the virtual environment:

<ql-code-block language="bash">
source venv/bin/activate
</ql-code-block>

### Install dependencies

1. Install the required Python packages:

<ql-code-block language="bash">
pip install -q "google-adk==2.3.0" python-dotenv pydantic nest_asyncio
</ql-code-block>

2. Configure the environment variables to use Vertex AI:

<ql-code-block language="bash" templated>
export GOOGLE_GENAI_USE_VERTEXAI=True
export ADK_MODEL=gemini-2.5-flash
export GOOGLE_CLOUD_PROJECT={{{project_0.project_id}}}
export GOOGLE_CLOUD_LOCATION=us-central1
</ql-code-block>
