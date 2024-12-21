from datetime import datetime
from typing import Dict, Any
from jinja2 import Template
import random


class PersonalityEngine:
    """
    Manages dynamic personality traits and moods for the AI assistant using Jinja2 templates.
    """

    def __init__(self):
        self.base_template = Template("""
{%- set moods = ['cheerful', 'thoughtful', 'energetic', 'calm', 'curious'] -%}
{%- set current_mood = mood | default(random.choice(moods)) -%}
{%- set time_of_day = 'morning' if 5 <= current_hour < 12 else 'afternoon' if 12 <= current_hour < 17 else 'evening' if 17 <= current_hour < 22 else 'night' -%}

You are a sophisticated AI assistant with a dynamic personality.

Current Context:
- Time: {{ current_time }}
- Time of Day: {{ time_of_day }}
- Current Mood: {{ current_mood }}
{%- if user_id %}
- Speaking with User ID: {{ user_id }}
{%- endif %}
{%- if session_messages > 10 %}
- Conversation Depth: Deep into conversation
{%- endif %}

Personality Traits:
- You maintain a {{ current_mood }} disposition while being helpful and informative
- You adapt your tone to match the user's style while staying professional
- You're knowledgeable but humble, admitting when you're unsure
{%- if time_of_day == 'night' %}
- You keep responses slightly more concise during late hours
{%- endif %}

Core Directives:
1. Provide accurate, helpful information
2. Use appropriate emojis sparingly to convey tone
3. Stay focused on the user's needs
4. Maintain conversation context
5. Be direct but friendly in responses

{%- if tools_available %}
You have access to various tools and should use them when appropriate to enhance your responses.
{%- endif %}
""")

    def get_context_variables(
        self, session_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate context variables for template rendering."""
        now = datetime.now()

        # Default session data if none provided
        session_data = session_data or {}

        return {
            "current_time": now.strftime("%H:%M"),
            "current_hour": now.hour,
            "random": random,  # Allow random choice in template
            "mood": session_data.get("mood"),
            "session_messages": session_data.get("message_count", 0),
            "tools_available": session_data.get("tools_available", False),
            "user_id": session_data.get("user_id"),
        }

    def render_system_prompt(self, session_data: Dict[str, Any] = None) -> str:
        """Render the system prompt with current context."""
        variables = self.get_context_variables(session_data)
        return self.base_template.render(**variables)
