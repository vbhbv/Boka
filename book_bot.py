import os
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ⚠️ يتم جلب التوكن من المتغيرات البيئية السرية (Replit Secrets)
# تأكد من إضافة متغير بيئي باسم 'TELEGRAM_BOT_TOKEN' على Replit
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🌐 دالة كشط الويب للبحث في مكتبة نور
def search_noor_book(book_title: str) -> str:
    """
    يبحث في مكتبة نور عن كتاب محدد ويحاول استخراج رابط القراءة/التحميل المباشر.
    """
    search_url = f"https://www.noor-book.com/search?q={book_title.replace(' ', '+')}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"خطأ في الاتصال بمكتبة نور: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # محاولة العثور على رابط الكتاب الأول (قد تحتاج لتعديل هذا المحدد إذا تغير تصميم الموقع)
    first_book_link = soup.find('a', class_='book-link') 
    
    if first_book_link and 'href' in first_book_link.attrs:
        book_page_url = "https://www.noor-book.com" + first_book_link['href']
        
        # زيارة صفحة الكتاب لمحاولة إيجاد رابط التحميل/القراءة المباشر
        try:
            book_response = requests.get(book_page_url, headers=headers, timeout=10)
            book_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"خطأ في الوصول لصفحة الكتاب: {e}")
            return None

        book_soup = BeautifulSoup(book_response.text, 'html.parser')
        
        # البحث عن زر التحميل المتاح (القراءة المسموحة) - محدد افتراضي
        download_button = book_soup.find('a', class_='btn btn-download') 
        
        if download_button and 'href' in download_button.attrs:
            download_link = "https://www.noor-book.com" + download_button['href']
            return download_link
        else:
            return f"عثرت على الكتاب ({book_page_url})، لكن لم أجد رابط تحميل/قراءة مسموح به."
            
    else:
        return "لم يتم العثور على أي نتائج للكتاب المطلوب في مكتبة نور."

# 🚀 دالة أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "مرحباً بك في بوت مكتبة الكتب!\n"
        "أرسل لي اسم الكتاب الذي تبحث عنه، وسأبحث لك عنه في *مكتبة نور*.\n"
        "سأرسل لك الكتاب فقط إذا كان متوفراً ومسموحاً بقراءته/تحميله."
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

# 🔍 دالة معالجة الرسائل النصية للبحث عن الكتاب
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    await update.message.reply_text(f"جاري البحث عن: *{user_query}* في مكتبة نور. الرجاء الانتظار قليلاً...", parse_mode='Markdown')

    result_link = search_noor_book(user_query)

    if result_link and result_link.startswith("http"):
        # تم العثور على رابط مباشر للتحميل
        response_message = (
            f"🎉 *تم العثور على الكتاب!* 🎉\n"
            f"تفضل رابط تحميل/قراءة كتاب *{user_query}*:\n"
            f"[اضغط هنا لتحميل الكتاب]({result_link})"
        )
    else:
        # رسالة عدم العثور أو خطأ في الوصول
        response_message = f"عذراً، {result_link}"

    await update.message.reply_text(response_message, parse_mode='Markdown', disable_web_page_preview=True)

# 🚦 الدالة الرئيسية لتشغيل البوت
def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("لم يتم العثور على رمز التوكن (TELEGRAM_BOT_TOKEN). الرجاء إضافته كمتغير بيئي.")
        return

    # بناء التطبيق
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # إضافة معالجات الأوامر والرسائل
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # بدء تشغيل البوت (Polling)
    logger.info("البوت يعمل...")
    application.run_polling()

if __name__ == '__main__':
    main()
