"""
Test script to verify function calling approach works with Gemini
"""

import os
import sys
import json

# Add parent directory to path FIRST before any other imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Load environment variables from parent directory .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, '.env'))

from google import genai
from google.genai import types
# from utils.logger import logger  # Commented out for testing

# Simple test function schema
TEST_FUNCTION = types.FunctionDeclaration(
    name="submit_player_info",
    description="Submit the player information found",
    parameters={
        "type": "object",
        "properties": {
            "player_name": {
                "type": "string",
                "description": "Full name of the player"
            },
            "sport": {
                "type": "string",
                "description": "The sport they play"
            },
            "school": {
                "type": "string",
                "description": "Their high school"
            },
            "star_rating": {
                "type": "number",
                "description": "Star rating if found"
            },
            "offers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of college offers"
            },
            "sources_used": {
                "type": "array",
                "items": {"type": "string"},
                "description": "URLs that were searched"
            }
        },
        "required": ["player_name"]
    }
)

def test_function_calling():
    """Test that we can use grounded search + function calling together"""

    print("=" * 60)
    print("Testing Function Calling with Grounded Search")
    print("=" * 60)

    client = genai.Client(
        vertexai=True,
        project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        location=os.environ.get('GOOGLE_CLOUD_LOCATION')
    )

    # Test prompt
    prompt = """
    Use grounded search to find information about Arch Manning (quarterback).

    After searching, call the submit_player_info function with:
    - His full name
    - Sport (football)
    - Current high school
    - Star rating from recruiting sites
    - A few of his college offers
    - The sources you found

    Make sure to actually search for current information first, then structure it.
    """

    # Create tools list with BOTH grounded search AND our function
    tools = [
        types.Tool(google_search=types.GoogleSearch()),
        types.Tool(function_declarations=[TEST_FUNCTION])
    ]

    print("\nCalling Gemini with:")
    print("- Grounded search tool")
    print("- Custom function schema")
    print("\nPrompt:", prompt[:100] + "...")

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                tools=tools,
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode="any",  # Use string instead of enum
                        allowed_function_names=["submit_player_info"]
                    )
                )
            )
        )

        print("\n✅ API call succeeded!")

        # Extract the function call
        if response.candidates:
            candidate = response.candidates[0]

            # Debug: Show what we got back
            print("\nResponse parts:")
            if hasattr(candidate.content, 'parts'):
                for i, part in enumerate(candidate.content.parts):
                    if hasattr(part, 'text') and part.text:
                        print(f"  Part {i}: Text content (length: {len(part.text)})")
                    if hasattr(part, 'function_call') and part.function_call:
                        print(f"  Part {i}: Function call - {part.function_call.name}")

                        if part.function_call.name == "submit_player_info":
                            structured_data = dict(part.function_call.args)
                            print("\n🎯 Successfully extracted structured data!")
                            print("\nStructured Output:")
                            print(json.dumps(structured_data, indent=2))

                            # Check if grounding actually happened
                            if hasattr(candidate, 'grounding_metadata'):
                                print("\n✅ Grounding metadata present - search was performed!")
                                if hasattr(candidate.grounding_metadata, 'grounding_chunks'):
                                    chunks = candidate.grounding_metadata.grounding_chunks
                                    print(f"   Found {len(chunks) if chunks else 0} grounding chunks")
                            else:
                                print("\n⚠️  No grounding metadata found")

                            return structured_data

            print("\n❌ No function call found in response")
        else:
            print("\n❌ No candidates in response")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

    return None


if __name__ == "__main__":
    # Make sure env vars are set
    if not os.environ.get('GOOGLE_CLOUD_PROJECT'):
        print("⚠️  GOOGLE_CLOUD_PROJECT not set!")
    if not os.environ.get('GOOGLE_CLOUD_LOCATION'):
        print("⚠️  GOOGLE_CLOUD_LOCATION not set!")

    result = test_function_calling()

    print("\n" + "=" * 60)
    if result:
        print("✅ TEST PASSED - Function calling with grounded search works!")
    else:
        print("❌ TEST FAILED - Check the output above for details")