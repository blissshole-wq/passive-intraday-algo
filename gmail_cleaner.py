import imaplib
import email
from datetime import datetime, timedelta

# --- 1. உங்க ஜிமெயில் ஐடியை மட்டும் இங்கே போடுங்க ப்ரோ ---
EMAIL_USER = "spalanikumarr@gmail.com"  # 👈 உங்க ஜிமெயில் ஐடியை மட்டும் மாத்துங்க

print("=" * 60)
print("🔑 GMAIL SECURE AUTHENTICATION SYSTEM")
print("=" * 60)

# கோடு ரன் ஆனதும் டெர்மினலிலேயே பாஸ்வேர்ட் கேட்கும் வசதி!
EMAIL_PASS = input("👉 உங்க 16 டிஜிட் கூகுள் ஆப் பாஸ்வேர்டை இங்கே பேஸ்ட் பண்ணுங்க: ").strip()

def clean_gmail_folder(folder_name, search_criterion="ALL"):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        
        status, messages = mail.select(folder_name)
        if status != "OK":
            print(f"❌ {folder_name} ஃபோல்டரை ஓபன் பண்ண முடியல ப்ரோ!")
            return

        status, search_data = mail.search(None, str(search_criterion))
        mail_ids = search_data[0].split()
        
        total_mails = len(mail_ids)
        print(f"🔍 {folder_name}-ல் மொத்தம் {total_mails} குப்பை மெயில்கள் இருக்கு.")

        if total_mails == 0:
            mail.logout()
            return

        count = 0
        for m_id in mail_ids:
            mail.store(m_id, '+FLAGS', '\\Deleted')
            count += 1

        mail.expunge()
        mail.logout()
        print(f"✅ சக்சஸ்! {folder_name}-ல் இருந்து {count} மெயில்கள் காலி!!!")
        
    except Exception as e:
        print(f"⚠️ லாகின் செய்ய முடியவில்லை: {e}\n(பாஸ்வேர்ட் தப்பாக இருக்கலாம் ப்ரோ!)")

if __name__ == "__main__":
    if not EMAIL_PASS:
        print("❌ பாஸ்வேர்ட் கொடுக்காமல் கோடை ரன் பண்ண முடியாது ப்ரோ!")
        exit()
        
    print("\n🚀 ஜிமெயில் ஆட்டோ-க்ளீனர் இன்ஜின் வேலை செய்யத் தொடங்குகிறது...\n")
    
    target_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    promo_query = f'X-GM-RAW "category:promotions before:{target_date}"'
    
    # க்ளீனிங் ஆப்ஷன்கள்
    clean_gmail_folder('"[Gmail]/Spam"', "ALL")
    clean_gmail_folder('"[Gmail]/Trash"', "ALL")
    clean_gmail_folder('"[Gmail]/All Mail"', promo_query)

    print("\n🏁 க்ளீனிங் வேலைகள் அனைத்தும் முடிவடைந்தது ப்ரோ!")