import random
import logging
import asyncio

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Сценарий с шагами квеста
quest_steps = [
    {
        "text": """Моросит дождь, размывая собянинские газоны, промокшие дворники роняют свои слезы, пока ты выползаешь из-под одеяла. Отличный день, чтобы остаться дома и гладить кошку. Ты выходишь из комнаты и видишь на кухонном столе странную светящуюся коробочку с надписью "Открой меня"
        \n"""
                "A) Люблю коробочки! Возьму ее, вдруг внутри окажется сырок\n"
                "Б) Хм, какая продолговатая коробочка, возможно получится надеть ее на себя\n"
                "В) Пока пораздупляюсь, посмотрю в окошку, налью себе чай в большую кружку, а потом посмотрим",
        "choices": [
            ("A", 1),
            ("Б", 1),
            ("В", 0)
        ]
    },
    {
        "text": """Тебя так и манит эта коробочка, поэтому ты не выдерживаешь. Ну что же, не успел ты ее распаковать, как она топологически-гомеоморфно выворачивается в тесеракт и заполняет собою все пространство кухни. 
        \nТы в ловушке коробочкового куба. Можешь кричать сколько угодно, в параллельной вселенной сырков пока не изобрели.
        \nИсследуя физические свойства коробочки, ты замечаешь, что звук попадает и отражается от граней, превращаясь в красные лазерные лучи. Ломаные линии лазера высвечивают перед тобой на стене надпись "Добро пожаловать в симулятор свиданий 3000! Благодарим вас за приобретение подписки PRO+. Как вы знаете из правил пользовательского соглашения, пользователь имеет право сходить на одно свидание с цифровой версией Ани Сметаниной, выдаваемой на Госуслугах.
        \nВ случае успешного прохождения, пользователь получает в распоряжение согласие настоящей Ани Сметаниной на последующее проведение свидания в мире с [seed=393514585195, lang=ru, timezone=Moscow, Russia].
        \nВ случае провала пользователь вносится в реестр повесток и получает соответствующее уведомление и обязуется находиться в коробочке, программируя боевых дронов в течение двух лет"\n Из стены выезжает постамент с кнопкой "согласиться":\n"""
                "A) [Альфа] Уверенно нажимаю кнопку, не прислуживая ей\n"
                "Б) Эй, а где кнопка Отказаться??? ПОНЯТНО-ПОНЯТНО\n"
                "В) Разумеется соглашаюсь, звучит как веселое приключение",
        "choices": [
            ("A", "dice_roll_alpha"),
            ("Б", 0),
            ("В", 1)
        ]
    },
    {
        "text": """ВЖУХ! ВЖУХ! ВЖУХ! Цифры высокоранговой матрицы начинают выбегать по ткани пространства до тех пор, пока стрим байтов не заканчивает передачу и не конвертируется в объемную версию Ани Сметаниной.\nОна недовольно окидывает тебя взглядом с ног до головы и поджимает губы. Кажется, у нее нет никаких воспоминаний о встрече с тобой. "Ну что там ещё? Быстрее говори, пожалуйста, у меня нет на тебя времени"\n"""
                "A) [Харизма] Намекаю ей, что пришел сюда, чтобы починить фильтр для воды\n"
                "Б) Опускаю голову слегка вниз и смиренно спрашиваю, чем я могу быть полезен\n"
                "В) Молчу и переминаюсь с ноги на ногу",
        "choices": [
            ("A", "dice_roll_charisma"),
            ("Б", 1),
            ("В", 0)
        ]
    },
    {
        "text": "*Аня продолжает с сомнением на тебя смотреть, но уже благожелательнее* "
                "Кажется, ты ее заинтересовал. Вдруг ты замечаешь, что позади Ани материализовывается стол с едой. Может, она проголодалась?\n"
                "A) Метнусь кабанчиком и принесу ей французский хот-дог с сосиской из индейки, пюрешку и салат с помидорами и огурцами\n"
                "Б) Попробую набрать разную еду, откуда мне знать, что она ест\n"
                "В) Ммм, что тут у нас...луковый суп? Пахнет очень аппетитно",
        "choices": [
            ("A", 1),
            ("Б", 0),
            ("В", -1000)
        ]
    },
    {
        "text": "Ням! Кажется, она больше не голодна. А ПОПИТЬ НЕ ПРИНЕС?\n"
                "A) Вода в стакане из Макдональдса: беспроигрышный вариант\n"
                "Б) Конечно принес, вот яблочный сидр, пусть пьет его, а потом схожу за ещё одним\n"
                "В) Американо",
        "choices": [
            ("A", 0),
            ("Б", 1),
            ("В", -1)
        ]
    },
    {
        "text": "По комнате пошёл вайб уютного дымка, Аня улыбается и тебе тоже становится весело и прикольно. Кажется, пора начать ненавязчиво подкатывать. Вы обсуждаете фильмы. Что предложишь посмотреть?\n"
                "A) Зайду с категории Б: как насчет Майора Грома?\n"
                "Б) Может быть, прохождение фростпанка за инженеров?\n"
                "В) Generation Pi, хороший фильм, давно не смотрели на четверге",
        "choices": [
            ("A", 1),
            ("Б", 1),
            ("В", 0)
        ]
    },
    {
        "text": "*Аня почти согласилась посмотреть с тобой фильм* Но может быть, сначала стоит впечатлить ее интеллектом? Вдруг она совершенно случайно сапиосексуальна?"
                """Она закатывает глаза: Антону нравятся числа {2, 4, 6, 8, 10, 12, 14, 16, 18, 20}. 
                \nА Маше: {3, 6, 9, 12, 15, 18, 21, 24, 27, 30}. 
                
                \nИзвестно, что если Стасу нравится некоторое натуральное число, то оно нравится и Антону. А если некоторое натуральное число нравится Маше, то Стасу оно точно не нравится. 
                
                \nУкажите наибольшее возможное количество чисел, которые нравятся Стасу. \n"""
                "A) 5\n"
                "Б) 6\n"
                "В) 7\n"
                "Г) [Интеллект] Решу в уме\n",
        "choices": [
            ("A", -2),
            ("Б", -2),
            ("В", 2),
            ("Г", "dice_roll_intelligence")
        ]
    },
    {
        "text": "Пу-пу-пу! Сапиосексуальность оставим для просмотра образовательных видео по CUDA. Вы легли на самую удобную в мире кровать посмотреть фильм. Пока ты скачиваешь видеокамтент, Аня отвлекается на погладить кошку. Наступает момент тишины. Что будешь делать?\n"
                "A) [Харизма] Сделаю комплимент её очень красивым скулам\n"
                "Б) [Альфа] Уверенно сообщу, что у меня нет пижамы\n"
                "В) Промолчу",
        "choices": [
            ("A", "dice_roll_charisma"),
            ("Б", "dice_roll_alpha"),
            ("В", 0)
        ]
    },
    {
        "text": "Не знаю, как ты это делаешь, но атмосфера становится все более хорни!) Всё как-то выруливает на обсуждение кинков. Твоя реакция:\n"
                "A) Да ну, странная внезапная херня, поясняю, что 99% людей это совершенно неинтересно. Лучше бы смотрели обзоры на строительство каркасных домов, я считаю\n"
                "Б) ****инг не одобряем, для всего остального оставлю пространство для экспериментов, мяв\n"
                "В) *Думает о коробочке, в которой лежат красный лак, стек и кошачьи ушки* Покажу ей аниме-картинки про фембоев",
        "choices": [
            ("A", 0),
            ("Б", 1),
            ("В", 2)
        ]
    },
    {
        "text": "Ну что, вы подошли к завершению фильма. Чем займемся в финальную стадию свидания?\n"
                "A) [Альфа] Сделать неприличный НАМЁК и предложить массаж со свечками\n"
                "Б) Чмокнуть её в носик и накрыть одеялком, а самому лечь, свернувшись калачиком на ковре. Пусть киса отдыхает\n"
                "В) Покажу ей все мои предметы, изготовленные на мастер-классах",
        "choices": [
            ("A", "dice_roll_alpha"),
            ("Б", 1),
            ("В", 0)
        ]
    }
]

# Отслеживание состояния пользователя и сохранение сообщений для последующего удаления
user_data = {}


# Функция для удаления всех предыдущих сообщений при перезапуске игры
async def clear_previous_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_ids: list):
    for message_id in message_ids:
        try:
            await context.bot.delete_message(chat_id, message_id)
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения: {e}")


# Функция выбора навыка в начале игры + отправка ссылки на музыку
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Очищаем предыдущие сообщения
        if "messages" in user_data.get(user_id, {}):
            await clear_previous_messages(context, chat_id, user_data[user_id]["messages"])

        # Сбрасываем данные пользователя
        user_data[user_id] = {"points": 0, "step": 0, "skill": None, "messages": []}

        # Отправка ссылки на музыку в начале
        music_path = "listen_to_me.mp3"
        with open(music_path, 'rb') as music:
            msg = await update.message.reply_audio(music, title="")
            user_data[user_id]["messages"].append(msg.message_id)


        user_data[user_id]["messages"].append(msg.message_id)

        keyboard = [
            [InlineKeyboardButton("Харизма", callback_data="skill_charisma")],
            [InlineKeyboardButton("Интеллект", callback_data="skill_intelligence")],
            [InlineKeyboardButton("Альфа-поведение", callback_data="skill_alpha")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = await update.message.reply_text("""Холодным промозглым осенним утром ты просыпаешься в своей теплой кроватке. 
        \nНа телефоне одно новое сообщение от пользователя <Белочка>. Ты открываешь телеграм и 一  ВАУ! Оо 一  добрая белочка сегодня в хорошем настроении и дарит тебе 1 бонусный навык:
                                              """, reply_markup=reply_markup)

        # Сохраняем сообщение для последующего удаления
        user_data[user_id]["messages"].append(msg.message_id)

    except Exception as e:
        logger.error(f"Error in start function: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова.")


# Функция для обработки выбора навыка
async def choose_skill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    skill = query.data.split('_')[1]
    user_data[user_id]["skill"] = skill
    await query.answer()

    msg = await query.message.reply_text(f"Ты получаешь: {skill.capitalize()}. Возможно этот скилл тебе пригодится...")
    user_data[user_id]["messages"].append(msg.message_id)

    await ask_step(query, context)


# Функция для обработки шагов квеста
async def ask_step(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    user_id = update_or_query.from_user.id
    step_index = user_data[user_id]["step"]
    chat_id = update_or_query.from_user.id


    if step_index < len(quest_steps):
        step = quest_steps[step_index]
        keyboard = [
            [InlineKeyboardButton(opt[0], callback_data=str(i)) for i, opt in enumerate(step["choices"])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)


        if hasattr(update_or_query, 'message'):
            msg = await update_or_query.message.reply_text(step["text"], reply_markup=reply_markup)
        else:
            msg = await update_or_query.message.reply_text(step["text"], reply_markup=reply_markup)

        # Сохраняем ID сообщения для последующего удаления
        user_data[user_id]["messages"].append(msg.message_id)
    else:
        await calculate_ending(update_or_query, context)


# Основная функция обработки кнопок и квеста
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    await query.answer()

    if query.data.startswith("skill_"):
        await choose_skill(update, context)
        return

    if query.data == "restart":
        await restart(update, context)
        return

    step_index = user_data[user_id]["step"]

    try:
        choice_data = quest_steps[step_index]["choices"][int(query.data)][1]
    except (IndexError, ValueError):
        msg = await query.message.reply_text("Ошибка: Неправильный выбор, попробуйте снова.")
        user_data[user_id]["messages"].append(msg.message_id)
        return

    if isinstance(choice_data, str) and "dice_roll" in choice_data:
        skill = user_data[user_id]["skill"]
        roll = random.randint(1, 20)
        bonus = 0

        if skill == "charisma" and "charisma" in choice_data:
            bonus = 5
        elif skill == "intelligence" and "intelligence" in choice_data:
            bonus = 5
        elif skill == "alpha" and "alpha" in choice_data:
            bonus = 5

        total_roll = roll + bonus
        msg = await query.message.reply_text(f"Вы бросили кубик... Выпало: {roll} + {bonus} (бонус) = {total_roll}!")
        user_data[user_id]["messages"].append(msg.message_id)

        if total_roll >= 15:
            user_data[user_id]["points"] += 2
            msg = await query.message.reply_text("Успешный успех! Великолепно.")
        elif total_roll >= 10:
            user_data[user_id]["points"] += 1
            msg = await query.message.reply_text("Успешно, но не 12 из 10.")
        else:
            msg = await query.message.reply_text("Неудачно... Видимо, не повезло, в следующий раз повезет больше.")

        user_data[user_id]["messages"].append(msg.message_id)

    else:
        user_data[user_id]["points"] += choice_data

    user_data[user_id]["step"] += 1

    if user_data[user_id]["step"] < len(quest_steps):
        await ask_step(query, context)
    else:
        await calculate_ending(query, context)


# Функция подсчёта очков и финала с self-destructing картинками
async def calculate_ending(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    user_id = update_or_query.from_user.id
    points = user_data[user_id]["points"]

    if points >= 12:
        ending = f"""Поздравляем! Вы только что провели восхитительное свидание, и, похоже, даже цифровая кошка дала вам замурчательное одобрение. 
                 \nАня улыбается так, что вы уже чувствуете: дело близится к тому самому моменту. 
                 \nВсё просто идеально! Выходя из тесеракта, гасите свет, скриншотьте результат и предъявляйте при встрече для получения свидания ИРЛ\nНабранные очки: {points}"""
        photo_path = "happy_ending.png"  # Картинка для хорошей концовки
    elif points >= 5:
        ending = f"""Ну что ж, свидание прошло... нормально. То есть, не то чтобы она стонет от неземного удовольствия, 
                         \nно и двери перед вами не захлопнула. Что-то явно пошло не так, но шанс есть. Возможно. 
                         \nПопробуйте не рассказывать в следующий раз про каркасные дома.\nНабранные очки: {points}"""
        photo_path = "neutral_ending.png"  # Картинка для нейтральной концовки
    elif points <= -900:
        ending = f"НИКОГДА. БОЛЬШЕ. ТАК. НЕ. ДЕЛАЙ. ПОЛНЫЙ ПРОВАЛ. \nНабранные очки: {points}"
    else:
        ending = f"""Ох... ну... это было... уникально, скажем так. Может, вы просто созданы для мира виртуальных встреч? 
                 \nАня уже заблокировала вас на Госуслугах.
                 \bНу что ж, зато теперь у вас найдется время пересмотреть свои тактики и, возможно, проанализировать самого себя, пока проектируете боевых роботов.\nНабранные очки: {points}"""
        photo_path = "bad_ending.png"  # Картинка для плохой концовки

    keyboard = [[InlineKeyboardButton("Начать заново", callback_data="restart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = await update_or_query.message.reply_text(ending, reply_markup=reply_markup)
    user_data[user_id]["messages"].append(msg.message_id)

    with open(photo_path, 'rb') as photo:
        sent_message = await update_or_query.message.reply_photo(photo)
        user_data[user_id]["messages"].append(sent_message.message_id)



# Обработчик для кнопки "Начать заново"
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


# Глобальный обработчик ошибок
async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    try:
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова.")
    except Exception as e:
        logger.error(f"Error sending error message: {e}")


if __name__ == '__main__':
    application = ApplicationBuilder().token("8166145006:AAGtrIoueS1eg3GFd_oVTajAxgxzqYfHEwE").build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_error_handler(handle_error)

    application.run_polling()
