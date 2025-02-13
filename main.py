import streamlit as st
import json
import requests
from typing import Optional

class LangflowAPI:
    def __init__(self, base_url: str = "http://127.0.0.1:7860"):
        self.base_url = base_url
        self.flow_id = "99e0375a-7497-4f95-a19d-20d4e6d5c23a"  # Default flow ID
        
    def run_flow(self,
                 message: str,
                 endpoint: str,
                 output_type: str = "chat",
                 input_type: str = "chat",
                 tweaks: Optional[dict] = None) -> dict:
        
        api_url = f"{self.base_url}/api/v1/run/{endpoint}"
        payload = {
            "input_value": message,
            "output_type": output_type,
            "input_type": input_type,
        }
        headers = None
        
        if tweaks:
            payload["tweaks"] = tweaks

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

def extract_message_content(response: dict) -> str:
    """Extract the actual message content from the nested JSON response"""
    try:
        # Navigate through the nested structure
        if "outputs" in response:
            outputs = response["outputs"]
            if outputs and len(outputs) > 0:
                first_output = outputs[0]
                if "outputs" in first_output:
                    inner_outputs = first_output["outputs"]
                    if inner_outputs and len(inner_outputs) > 0:
                        if "messages" in inner_outputs[0]:
                            messages = inner_outputs[0]["messages"]
                            if messages and len(messages) > 0:
                                return messages[0]["message"]
        
        # If we couldn't find the message in the expected structure,
        # return the full response as a formatted string
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error parsing response: {str(e)}"

def main():
    st.set_page_config(page_title="AlgOracle", layout="wide")
    st.title("AlgOracle")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        base_url = "http://127.0.0.1:7860"
        flow_id = "99e0375a-7497-4f95-a19d-20d4e6d5c23a"
        
        # Advanced settings expander
        with st.expander("Advanced Settings"):
            output_type = st.selectbox("Output Type", ["chat", "text", "json"], index=0)
            input_type = st.selectbox("Input Type", ["chat", "text", "json"], index=0)
            
            # Tweaks editor
            st.subheader("Tweaks")
            tweaks_str = json.dumps({
                    "ChatInput-FxBDE": {},
                    "Agent-HnfcF": {},
                    "Prompt-tam51": {},
                    "ChatOutput-UuLpB": {},
                    "TavilySearchComponent-KsdLl": {}
                }, indent=2)
            
            try:
                tweaks = json.loads(tweaks_str)
            except json.JSONDecodeError:
                st.error("Invalid JSON in tweaks")
                tweaks = {}

            # Debug mode toggle
            debug_mode = st.checkbox("Debug Mode", value=False)

    # Initialize API client
    api_client = LangflowAPI(base_url)

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to ask?"):
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get response from Langflow
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = api_client.run_flow(
                    message=prompt,
                    endpoint=flow_id,
                    output_type=output_type,
                    input_type=input_type,
                    tweaks=tweaks
                )
                
                if "error" in response:
                    st.error(f"Error: {response['error']}")
                else:
                    # Extract and display the message content
                    message_content = extract_message_content(response)
                    st.write(message_content)
                    
                    # If debug mode is enabled, show the raw JSON response
                    if debug_mode:
                        with st.expander("Debug: Raw Response"):
                            st.json(response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": message_content})

    # Clear chat button
    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()