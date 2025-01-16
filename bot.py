import google.generativeai as genai
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import random
import time
from collections import defaultdict

# Configure your API key for Gemini
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Sample quiz categories and difficulty levels
categories = ["general knowledge", "sports", "history", "science", "movies"]
difficulty_levels = ["easy", "medium", "hard"]

# Dictionary to store user data
user_data = defaultdict(dict)

# Function to generate questions using Gemini
def generate_question(category, difficulty):
    prompt = f"Generate a {difficulty} quiz question in the category of {category} with 4 options."
    response = model.generate_content(prompt)
    question_data = response.text.split("\n")  # Split response into different lines
    question = question_data[0]  # First line will be the question
    options = question_data[1:5]  # The next 4 lines will be the options
    correct_answer = "B"  # Assume option B is always the correct answer (you can adjust this if the model provides an answer)
    return question, options, correct_answer

# Start Command: When a user starts the bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the Quiz Bot! 🎉 Type /quiz to start your quiz. 💡")

# Quiz Command: Starts a quiz for the user
def quiz(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id

    # Get difficulty level from user input
    difficulty = "medium"  # Default difficulty level
    if context.args:
        difficulty = context.args[0].lower()
        if difficulty not in difficulty_levels:
            update.message.reply_text(f"❌ Invalid difficulty level. Defaulting to 'medium'.")
            difficulty = "medium"

    # Randomly select a category
    category = random.choice(categories)
    # Generate a quiz question using Gemini
    question, options, correct_answer = generate_question(category, difficulty)
    
    # Store data in user_data
    user_data[user_id]['question'] = question
    user_data[user_id]['options'] = options
    user_data[user_id]['correct_answer'] = correct_answer
    user_data[user_id]['score'] = 0
    user_data[user_id]['streak'] = 0
    user_data[user_id]['hints_used'] = 0
    user_data[user_id]['quiz_started'] = True

    update.message.reply_text(f"Question: {question} 🤔\nOptions: {', '.join(options)}\n⏳ You have 15 seconds to answer! Type A, B, C, or D.")
    
    # Timer for the quiz
    time.sleep(15)  # 15 seconds for answering
    check_answer(update, context)

# Function to check user's answer
def check_answer(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id

    if 'quiz_started' not in user_data[user_id]:
        return  # If quiz wasn't started properly, return early

    # Check if the user has answered
    if 'answer' not in user_data[user_id]:
        update.message.reply_text(f"⏰ Time's up! The correct answer was {user_data[user_id]['correct_answer']}.\n🎯 Your score: {user_data[user_id]['score']}")
    else:
        if user_data[user_id]['answer'].upper() == user_data[user_id]['correct_answer']:
            user_data[user_id]['score'] += 1
            user_data[user_id]['streak'] += 1
            update.message.reply_text(f"🎉 Correct! Your score is {user_data[user_id]['score']} with a streak of {user_data[user_id]['streak']}! 🌟")
        else:
            update.message.reply_text(f"❌ Incorrect! The correct answer was {user_data[user_id]['correct_answer']}.\n🎯 Your score: {user_data[user_id]['score']}")
            user_data[user_id]['streak'] = 0  # Reset streak on wrong answer

    # Ask if the user wants to play again
    update.message.reply_text("🔄 Want to play again? Type /quiz to start a new quiz! 🤗")

# Function to handle user input for answers
def handle_answer(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id

    # Store user's answer
    user_data[user_id]['answer'] = update.message.text.strip().upper()

    # Check the answer after the user submits
    check_answer(update, context)

# Leaderboard Command: Shows the top scorers
def leaderboard(update: Update, context: CallbackContext):
    top_players = sorted(user_data.items(), key=lambda x: x[1].get('score', 0), reverse=True)
    leaderboard_message = "🏆 **Top Scorers** 🏆\n"
    for idx, (user_id, data) in enumerate(top_players[:5], 1):
        leaderboard_message += f"{idx}. {data.get('name', 'Anonymous')} - {data['score']} points 🏅\n"
    
    update.message.reply_text(leaderboard_message)

# Achievements/Badges: Track player achievements and streaks
def track_achievements(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id

    # Unlock streak achievements
    if user_data[user_id]['streak'] >= 5:
        update.message.reply_text("🎖️ Achievement Unlocked: 5 Correct Answers Streak! 🔥")

    # Unlock quiz participation badge
    if user_data[user_id]['score'] >= 10:
        update.message.reply_text("🏅 Achievement Unlocked: 10 Points Earned! 🌟")

# Daily Challenge Command: Allow users to participate in daily challenges
def daily_challenge(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id

    # Assign random challenges to users
    challenges = ["Answer 5 questions in a row correctly", "Score 10 points in one quiz", "Complete 3 quizzes in a day"]
    challenge = random.choice(challenges)

    update.message.reply_text(f"🎯 **Daily Challenge**: {challenge} 💪")

# Daily Spin: Spins a wheel for rewards (points or hints)
def daily_spin(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id

    rewards = ["+5 points", "1 free hint", "Unlock a bonus quiz", "Double points for next quiz"]
    reward = random.choice(rewards)

    if reward == "+5 points":
        user_data[user_id]['score'] += 5
    elif reward == "1 free hint":
        user_data[user_id]['hints_used'] += 1
    elif reward == "Unlock a bonus quiz":
        update.message.reply_text("🎁 You unlocked a **Bonus Quiz**! Type /bonusquiz to play!")
    elif reward == "Double points for next quiz":
        user_data[user_id]['next_quiz_multiplier'] = 2

    update.message.reply_text(f"🎉 You spun the wheel and won: {reward}! 🎰")

# Bonus Quiz Command: Allows users to play a bonus quiz
def bonus_quiz(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id

    if 'next_quiz_multiplier' in user_data[user_id]:
        user_data[user_id]['score'] *= user_data[user_id]['next_quiz_multiplier']
        update.message.reply_text(f"🚀 Bonus Quiz! Double points earned. Your score is now {user_data[user_id]['score']} points!")
    else:
        update.message.reply_text("❌ No bonus quiz available. Please spin the wheel first!")

# Personalized Profile Command: Users can set their nickname and avatar
def set_profile(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id

    if context.args:
        name = " ".join(context.args)
        user_data[user_id]['name'] = name
        update.message.reply_text(f"🖋️ Your name has been set to {name}! 🎉")
    else:
        update.message.reply_text("❌ Please provide a name after the command. Example: /setprofile John Doe.")

# Help Command: Displays bot instructions
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("""
Welcome to Quiz Bot! Here are some commands you can use:
1. /quiz - Start a new quiz 🎮
2. /leaderboard - See the top scorers 🏆
3. /setprofile <name> - Set your profile name 📝
4. /dailyspin - Spin the wheel for rewards 🎰
5. /dailychallenge - Participate in the daily challenge 🎯
6. /bonusquiz - Play a bonus quiz with extra rewards 🎁
7. /help - See this message again 📚
""")

# Main function to set up the Telegram bot
def main():
    # Set up the Updater with your bot's token
  updater = Updater("7579444917:AAEdnqC9yxAnY7aWrvZu_Cr8sK91vCT8hx0", use_context=True)

    # Add handlers for the commands
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("quiz", quiz))
    updater.dispatcher.add_handler(CommandHandler("leaderboard", leaderboard))
    updater.dispatcher.add_handler(CommandHandler("setprofile", set_profile))
    updater.dispatcher.add_handler(CommandHandler("dailyspin", daily_spin))
    updater.dispatcher.add_handler(CommandHandler("dailychallenge", daily_challenge))
    updater.dispatcher.add_handler(CommandHandler("bonusquiz", bonus_quiz))
    updater.dispatcher.add_handler(CommandHandler("help", help_command))

    # Handle user messages for answers
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_answer))

    # Start the bot to listen for incoming messages
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
