from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import re
from uuid import uuid4
import time
import asyncio
from contextlib import asynccontextmanager

router = APIRouter()

# Define the flag
FLAG = "flag{i_5ucc3ssfu1ly_x553d}"

PATH = "/chatroom/"

# Dictionary to store the messages
# Key: user ID, Value: tuple of (messages list, last access time)
messages: dict[str, tuple[list[str], float]] = {}

cleanup_task_instance = None

# Function to detect XSS patterns
def detect_xss(input_str: str) -> bool:
    xss_patterns = [
        r"<script.*?>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript URIs
        r"on\w+=",  # Inline event handlers (e.g., onclick)
        r"<.*?on\w+=.*?>",  # Inline event handlers in tags
    ]
    for pattern in xss_patterns:
        if re.search(pattern, input_str, re.IGNORECASE):
            return True
    return False

# Background task to clean up inactive chats
async def cleanup_task():
    print("Starting cleanup task...")
    while True:
        try:
            current_time = time.time()
            inactive_threshold = 5 * 60  # 5 minutes in seconds
            inactive_users = []
            
            for user_id, (_, last_access_time) in list(messages.items()):
                if current_time - last_access_time > inactive_threshold:
                    inactive_users.append(user_id)
            
            for user_id in inactive_users:
                messages.pop(user_id, None)
            
            if inactive_users:
                print(f"Cleaned up {len(inactive_users)} inactive chat sessions")
                
            # Run every 60 seconds
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)  # Continue even if there's an error

@router.on_event("startup")
async def startup_event():
    global cleanup_task_instance
    if cleanup_task_instance:
        cleanup_task_instance.cancel()

    cleanup_task_instance = asyncio.create_task(cleanup_task())

@router.on_event("shutdown")
async def shutdown_event():
    if cleanup_task_instance:
        cleanup_task_instance.cancel()

@router.get("/", response_class=HTMLResponse)
async def xss_practice(msg: str = Query(""), user: str = Query("")):
    if not user:
        user = str(uuid4())
        return HTMLResponse(
            content=f"<html><body><script>window.location.href = '{PATH}?user={user}'</script></body></html>"
        )
    
    # Add the new message to the user's message list if not empty
    if msg:
        if user not in messages:
            messages[user] = ([], time.time())
        messages[user][0].append(msg)
        messages[user] = (messages[user][0], time.time())

        return HTMLResponse(
            content=f"<html><body><script>window.location.href = '{PATH}?user={user}'</script></body></html>"
        )
    else:
        # Update last access time even if no new message
        if user in messages:
            messages[user] = (messages[user][0], time.time())
        else:
            messages[user] = ([], time.time())
    
    # Create the form with hidden user field
    form_html = f"""
    <form action="{PATH}" method="get">
        <input type="hidden" name="user" value="{user}">
        <label for="msg">Enter your message:</label>
        <input type="text" id="msg" name="msg">
        <input type="submit" value="Send">
    </form>
    """
    
    # Generate the chat display
    chat_html = "<div style='border: 1px solid #ccc; padding: 10px; margin-top: 20px; height: 300px; overflow-y: scroll;'>"
    chat_html += "<h3>Chat Messages:</h3>"
    
    # Display all messages from all users
    for chat_user, user_messages in messages.items():
        for user_msg in user_messages[0]:
            # Indicate if message is from current user
            sender = "You" if chat_user == user else f"User-{chat_user[:8]}"
            chat_html += f"<p><strong>{sender}:</strong> {user_msg}</p>"
            
            # Check for XSS in any message
            if detect_xss(user_msg):
                chat_html += f"<p style='color: red;'><strong>Alert:</strong> XSS detected in message!</p>"
                chat_html += f"<p style='color: green;'><strong>Flag:</strong> {FLAG}</p>"
    
    chat_html += "</div>"
    
    # Build complete response
    response = f"""
    <html>
    <head><title>Chatroom</title></head>
    <body>
        <h1>Chatroom Challenge</h1>
        {form_html}
        {chat_html}
    </body>
    </html>
    """
    
    return HTMLResponse(content=response)