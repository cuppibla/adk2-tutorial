<!-- Environment setup: structure follows ljhenne's agy001 house pattern -->
<!-- (Google Cloud setup section + ql-variable chips + templated exports + tf startup script). -->
<!-- Base preserved from Christina Lin's migration (CloudVLab bb0a8bb); the -->
<!-- "Enable the Vertex AI API" step moved into tf/ (runs at Start Lab). -->
<!-- ADK_MODEL added because the AI-Studio alias gemini-flash-latest 404s on Vertex. -->

## Google Cloud setup

![[/fragments/startqwiklab]]

![[/fragments/gcpconsole]]

![[/fragments/cloudshell]]

### Configure your environment

This lab created a project for you when you pressed **Start Lab**, assigned a region, and enabled the Vertex AI API in the background — there is nothing to enable by hand.

1. Note your assigned values:
   - **Project ID:** <ql-variable key="project_0.project_id" placeHolder="PROJECT"></ql-variable>
   - **Region:** <ql-variable key="project_0.default_region" placeHolder="REGION"></ql-variable>

2. In Cloud Shell, configure them in your environment:
   <ql-code-block bash templated noWrap>
   export GOOGLE_GENAI_USE_VERTEXAI=True
   export GOOGLE_CLOUD_PROJECT="{{{project_0.project_id | "PROJECT_ID"}}}"
   export GOOGLE_CLOUD_LOCATION="{{{project_0.default_region | "REGION"}}}"
   export ADK_MODEL=gemini-2.5-flash
   gcloud config set project $GOOGLE_CLOUD_PROJECT
   </ql-code-block>

## Task 1. Initialize your environment

In this task, you clone the tutorial repository, set up a Python virtual environment, and install the required libraries.

1. In Cloud Shell, clone the tutorial repository and enter it:

<ql-code-block language="bash">
git clone https://github.com/cuppibla/adk2-tutorial.git
cd adk2-tutorial
</ql-code-block>

2. Create and activate a Python virtual environment:

<ql-code-block language="bash">
python3 -m venv venv
source venv/bin/activate
</ql-code-block>

3. Install the required Python packages:

<ql-code-block language="bash">
pip install -q "google-adk==2.3.0" python-dotenv pydantic nest_asyncio
</ql-code-block>
