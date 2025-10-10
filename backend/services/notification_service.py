import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from models.models import User, Match, LostItem, FoundItem

class NotificationService:
    def __init__(self):
        self.email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.email_port = int(os.getenv('EMAIL_PORT', 587))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.enabled = bool(self.email_user and self.email_password)
    
    def send_match_notification(self, match: Match):
        """
        Send notification to both users when a match is found
        """
        if not self.enabled:
            print("Email notifications not configured, skipping...")
            return
        
        lost_item_owner = User.query.get(match.lost_item.user_id)
        found_item_owner = User.query.get(match.found_item.user_id)
        
        # Send notification to lost item owner
        self._send_match_email(
            lost_item_owner,
            match,
            is_lost_item_owner=True
        )
        
        # Send notification to found item owner
        self._send_match_email(
            found_item_owner,
            match,
            is_lost_item_owner=False
        )
    
    def _send_match_email(self, user: User, match: Match, is_lost_item_owner: bool):
        """
        Send match notification email to a user
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = user.email
            
            if is_lost_item_owner:
                msg['Subject'] = f"Potential Match Found for Your Lost Item: {match.lost_item.title}"
                email_body = self._create_lost_item_email_body(user, match)
            else:
                msg['Subject'] = f"Potential Match Found for Your Found Item: {match.found_item.title}"
                email_body = self._create_found_item_email_body(user, match)
            
            # Create HTML and text versions
            html_part = MIMEText(email_body['html'], 'html')
            text_part = MIMEText(email_body['text'], 'plain')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            print(f"Match notification sent to {user.email}")
            
        except Exception as e:
            print(f"Failed to send email to {user.email}: {str(e)}")
    
    def _create_lost_item_email_body(self, user: User, match: Match):
        """
        Create email body for lost item owner
        """
        similarity_percentage = int(match.similarity_score * 100)
        
        text = f"""
Hi {user.name},

Great news! We found a potential match for your lost item.

Your Lost Item:
- {match.lost_item.title}
- Category: {match.lost_item.category}
- Lost at: {match.lost_item.lost_location}
- Lost on: {match.lost_item.lost_date}

Potential Match Found:
- {match.found_item.title}
- Category: {match.found_item.category}
- Found at: {match.found_item.found_location}
- Found on: {match.found_item.found_date}
- Condition: {match.found_item.condition}

Match Confidence: {similarity_percentage}%

Description of found item: {match.found_item.description}

If you think this might be your item, please log in to your account to confirm or contact the finder.

Best regards,
Lost & Found AI Team
"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .item-card {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .lost-item {{ background-color: #fff3cd; }}
        .found-item {{ background-color: #d1ecf1; }}
        .confidence {{ font-size: 18px; font-weight: bold; color: #28a745; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Potential Match Found! 🎉</h1>
        </div>
        <div class="content">
            <p>Hi {user.name},</p>
            <p>Great news! We found a potential match for your lost item.</p>
            
            <div class="item-card lost-item">
                <h3>Your Lost Item</h3>
                <p><strong>{match.lost_item.title}</strong></p>
                <p>Category: {match.lost_item.category}</p>
                <p>Lost at: {match.lost_item.lost_location}</p>
                <p>Lost on: {match.lost_item.lost_date}</p>
            </div>
            
            <div class="item-card found-item">
                <h3>Potential Match Found</h3>
                <p><strong>{match.found_item.title}</strong></p>
                <p>Category: {match.found_item.category}</p>
                <p>Found at: {match.found_item.found_location}</p>
                <p>Found on: {match.found_item.found_date}</p>
                <p>Condition: {match.found_item.condition}</p>
                <p>Description: {match.found_item.description}</p>
            </div>
            
            <p class="confidence">Match Confidence: {similarity_percentage}%</p>
            
            <p>If you think this might be your item, please log in to your account to confirm or contact the finder.</p>
            
            <p>Best regards,<br>Lost & Found AI Team</p>
        </div>
    </div>
</body>
</html>
"""
        
        return {'text': text, 'html': html}
    
    def _create_found_item_email_body(self, user: User, match: Match):
        """
        Create email body for found item owner
        """
        similarity_percentage = int(match.similarity_score * 100)
        
        text = f"""
Hi {user.name},

We found a potential owner for the item you found!

Your Found Item:
- {match.found_item.title}
- Category: {match.found_item.category}
- Found at: {match.found_item.found_location}
- Found on: {match.found_item.found_date}

Potential Owner's Lost Item:
- {match.lost_item.title}
- Category: {match.lost_item.category}
- Lost at: {match.lost_item.lost_location}
- Lost on: {match.lost_item.lost_date}
- Reward: ${match.lost_item.reward_amount}

Match Confidence: {similarity_percentage}%

Description of lost item: {match.lost_item.description}

If you think this matches the item you found, please log in to your account to confirm.

Best regards,
Lost & Found AI Team
"""

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .header {{ background-color: #17a2b8; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .item-card {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .found-item {{ background-color: #d1ecf1; }}
        .lost-item {{ background-color: #fff3cd; }}
        .confidence {{ font-size: 18px; font-weight: bold; color: #28a745; }}
        .reward {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Potential Owner Found! 🎯</h1>
        </div>
        <div class="content">
            <p>Hi {user.name},</p>
            <p>We found a potential owner for the item you found!</p>
            
            <div class="item-card found-item">
                <h3>Your Found Item</h3>
                <p><strong>{match.found_item.title}</strong></p>
                <p>Category: {match.found_item.category}</p>
                <p>Found at: {match.found_item.found_location}</p>
                <p>Found on: {match.found_item.found_date}</p>
            </div>
            
            <div class="item-card lost-item">
                <h3>Potential Owner's Lost Item</h3>
                <p><strong>{match.lost_item.title}</strong></p>
                <p>Category: {match.lost_item.category}</p>
                <p>Lost at: {match.lost_item.lost_location}</p>
                <p>Lost on: {match.lost_item.lost_date}</p>
                <p class="reward">Reward: ${match.lost_item.reward_amount}</p>
                <p>Description: {match.lost_item.description}</p>
            </div>
            
            <p class="confidence">Match Confidence: {similarity_percentage}%</p>
            
            <p>If you think this matches the item you found, please log in to your account to confirm.</p>
            
            <p>Best regards,<br>Lost & Found AI Team</p>
        </div>
    </div>
</body>
</html>
"""
        
        return {'text': text, 'html': html}
    
    def send_match_confirmation_notification(self, match: Match, confirming_user: User):
        """
        Send notification when a match is confirmed
        """
        if not self.enabled:
            print("Email notifications not configured, skipping...")
            return
        
        lost_item_owner = User.query.get(match.lost_item.user_id)
        found_item_owner = User.query.get(match.found_item.user_id)
        
        # Send to the other user (not the one who confirmed)
        if confirming_user.id == lost_item_owner.id:
            self._send_confirmation_email(found_item_owner, match, "lost item owner")
        else:
            self._send_confirmation_email(lost_item_owner, match, "finder")
    
    def _send_confirmation_email(self, user: User, match: Match, confirmed_by: str):
        """
        Send match confirmation email
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = user.email
            msg['Subject'] = f"Match Confirmed - {match.lost_item.title}"
            
            text = f"""
Hi {user.name},

Great news! The match for the item "{match.lost_item.title}" has been confirmed by the {confirmed_by}.

Next Steps:
1. Contact each other to arrange the return
2. Verify the item details when you meet
3. Complete the exchange safely

Item Details:
- Title: {match.lost_item.title}
- Category: {match.lost_item.category}

Thank you for using Lost & Found AI!

Best regards,
Lost & Found AI Team
"""

            html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .success {{ background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Match Confirmed! ✅</h1>
        </div>
        <div class="content">
            <p>Hi {user.name},</p>
            
            <div class="success">
                <p><strong>Great news! The match for "{match.lost_item.title}" has been confirmed by the {confirmed_by}.</strong></p>
            </div>
            
            <h3>Next Steps:</h3>
            <ol>
                <li>Contact each other to arrange the return</li>
                <li>Verify the item details when you meet</li>
                <li>Complete the exchange safely</li>
            </ol>
            
            <p>Thank you for using Lost & Found AI!</p>
            
            <p>Best regards,<br>Lost & Found AI Team</p>
        </div>
    </div>
</body>
</html>
"""
            
            html_part = MIMEText(html, 'html')
            text_part = MIMEText(text, 'plain')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            print(f"Match confirmation notification sent to {user.email}")
            
        except Exception as e:
            print(f"Failed to send confirmation email to {user.email}: {str(e)}")

# Global instance
notification_service = NotificationService()