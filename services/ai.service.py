"""
Claude AI Service for generating summaries.

This module handles all interactions with the Anthropic Claude API.
Uses the latest Claude Sonnet 4.5 model for high-quality summaries.
"""

import logging
from typing import Optional, Dict, Any
import anthropic
from anthropic import AsyncAnthropic

from config import settings

logger = logging.getLogger(__name__)


class ClaudeAIService:
    """
    Service for interacting with Claude AI API.
    
    Handles:
    - Summary generation from messages
    - Different summary styles (standard, quick, detailed, etc.)
    - Error handling and retries
    """
    
    def __init__(self):
        """Initialize Claude AI client."""
        self.client = AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.claude_timeout,
        )
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        logger.info(f"Claude AI Service initialized with model: {self.model}")
    
    async def generate_summary(
        self,
        messages: list[str],
        summary_type: str = "standard",
        language: str = "he",
        custom_instructions: Optional[str] = None,
    ) -> str:
        """
        Generate a summary from a list of messages.
        
        Args:
            messages: List of message texts to summarize
            summary_type: Type of summary (standard, quick, detailed, decisions, questions)
            language: Language for the summary (he, en)
            custom_instructions: Optional custom instructions for the summary
            
        Returns:
            str: Generated summary text
            
        Raises:
            Exception: If API call fails
        """
        if not messages:
            return "לא נמצאו הודעות לסיכום." if language == "he" else "No messages to summarize."
        
        try:
            # Build the prompt based on summary type
            prompt = self._build_prompt(
                messages=messages,
                summary_type=summary_type,
                language=language,
                custom_instructions=custom_instructions,
            )
            
            logger.info(
                f"Generating {summary_type} summary for {len(messages)} messages "
                f"in {language}"
            )
            
            # Call Claude API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            
            # Extract summary text
            summary = response.content[0].text
            
            logger.info(f"Summary generated successfully ({len(summary)} chars)")
            return summary
            
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise Exception(f"שגיאה בחיבור ל-AI: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in summary generation: {e}")
            raise Exception(f"שגיאה בלתי צפויה: {str(e)}")
    
    def _build_prompt(
        self,
        messages: list[str],
        summary_type: str,
        language: str,
        custom_instructions: Optional[str],
    ) -> str:
        """
        Build the prompt for Claude based on summary type.
        
        Args:
            messages: List of message texts
            summary_type: Type of summary to generate
            language: Language for the summary
            custom_instructions: Optional custom instructions
            
        Returns:
            str: Complete prompt for Claude
        """
        # Join messages with newlines and numbering
        messages_text = "\n".join(
            f"{i+1}. {msg}" for i, msg in enumerate(messages)
        )
        
        # Get instructions based on summary type
        instructions = self._get_summary_instructions(summary_type, language)
        
        # Add custom instructions if provided
        if custom_instructions:
            instructions += f"\n\nהנחיות נוספות: {custom_instructions}"
        
        # Build complete prompt
        prompt = f"""{instructions}

הודעות לסיכום ({len(messages)} הודעות):

{messages_text}

אנא צור סיכום לפי ההנחיות לעיל."""
        
        return prompt
    
    def _get_summary_instructions(self, summary_type: str, language: str) -> str:
        """
        Get instructions for different summary types.
        
        Args:
            summary_type: Type of summary
            language: Language for instructions
            
        Returns:
            str: Instructions text
        """
        if language == "he":
            instructions_map = {
                "standard": """אתה עוזר AI המתמחה בסיכום שיחות בקבוצות טלגרם.
צור סיכום תמציתי וברור של השיחה הבאה.

דרישות:
- 5-6 נקודות מרכזיות
- כל נקודה במשפט קצר וממוקד
- התחל כל נקודה עם emoji רלוונטי
- השתמש בעברית פשוטה וברורה
- התעלם מהודעות ספאם, שלום/שלום, או תוכן לא רלוונטי
- התמקד בתוכן המהותי והחשוב

פורמט:
📌 סיכום השיחה:
🔹 נקודה ראשונה
🔹 נקודה שנייה
🔹 נקודה שלישית
וכן הלאה...""",

                "quick": """צור סיכום קצר ומהיר של השיחה.

דרישות:
- 2-3 נקודות מרכזיות בלבד
- משפטים קצרים מאוד
- ללא emoji
- רק המידע החשוב ביותר

פורמט פשוט:
• נקודה 1
• נקודה 2
• נקודה 3""",

                "detailed": """צור סיכום מפורט ומעמיק של השיחה.

דרישות:
- 8-10 נקודות
- כל נקודה עם הסבר קצר
- כלול ציטוטים חשובים במרכאות אם רלוונטי
- ארגן לפי נושאים אם אפשר
- הוסף emoji לכל נושא

פורמט:
📌 סיכום מפורט:

📍 נושא ראשון:
   • פרט 1
   • פרט 2

📍 נושא שני:
   • פרט 1
   • פרט 2""",

                "decisions": """מצא והדגש החלטות שהתקבלו בשיחה.

דרישות:
- חלץ רק החלטות ברורות
- מי קיבל את ההחלטה אם ידוע
- מה ההחלטה
- פעולות שצריך לבצע

פורמט:
✅ החלטות שהתקבלו:
1. החלטה ראשונה - מי החליט, מה צריך לעשות
2. החלטה שנייה - מי החליט, מה צריך לעשות

אם לא היו החלטות ברורות, כתוב: "לא זוהו החלטות ברורות בשיחה.""",

                "questions": """מצא שאלות שנשארו פתוחות בשיחה.

דרישות:
- זהה שאלות שלא קיבלו תשובה
- שאלות שנדרשות החלטה או פעולה
- ארגן לפי חשיבות

פורמט:
❓ שאלות פתוחות:
1. שאלה ראשונה - מי שאל
2. שאלה שנייה - מי שאל
3. שאלה שלישית - מי שאל

אם כל השאלות נענו, כתוב: "כל השאלות קיבלו תשובות.""",
            }
        else:  # English
            instructions_map = {
                "standard": """You are an AI assistant specialized in summarizing Telegram group conversations.
Create a concise and clear summary of the following conversation.

Requirements:
- 5-6 main points
- Each point in a short, focused sentence
- Start each point with a relevant emoji
- Use simple, clear English
- Ignore spam, greetings, or irrelevant content
- Focus on substantial and important content

Format:
📌 Conversation Summary:
🔹 First point
🔹 Second point
🔹 Third point
etc...""",

                "quick": """Create a quick summary of the conversation.

Requirements:
- Only 2-3 main points
- Very short sentences
- No emojis
- Only the most important info

Simple format:
• Point 1
• Point 2
• Point 3""",

                "detailed": """Create a detailed and in-depth summary.

Requirements:
- 8-10 points
- Each point with brief explanation
- Include important quotes if relevant
- Organize by topics if possible
- Add emoji for each topic

Format:
📌 Detailed Summary:

📍 First topic:
   • Detail 1
   • Detail 2

📍 Second topic:
   • Detail 1
   • Detail 2""",

                "decisions": """Find and highlight decisions made in the conversation.

Requirements:
- Extract only clear decisions
- Who made the decision if known
- What the decision is
- Actions needed

Format:
✅ Decisions Made:
1. First decision - who decided, what to do
2. Second decision - who decided, what to do

If no clear decisions, write: "No clear decisions identified.""",

                "questions": """Find open questions in the conversation.

Requirements:
- Identify unanswered questions
- Questions requiring decision or action
- Organize by importance

Format:
❓ Open Questions:
1. First question - who asked
2. Second question - who asked
3. Third question - who asked

If all questions answered, write: "All questions were answered.""",
            }
        
        return instructions_map.get(summary_type, instructions_map["standard"])
    
    async def test_connection(self) -> bool:
        """
        Test connection to Claude API.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": "Hi"
                    }
                ]
            )
            logger.info("Claude API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Claude API connection test failed: {e}")
            return False
