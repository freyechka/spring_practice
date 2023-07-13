import discord
from discord.ext import commands
import config
import json
import os
import random
import requests
from bs4 import BeautifulSoup

"""Discord-бот, созданный при помощи библиотеки discord.py"""

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents, status=discord.Status.do_not_disturb)
bot.remove_command("help")

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}
url = 'https://www.forbes.ru/forbeslife/dosug/262327-na-vse-vremena-100-vdokhnovlyayushchikh-tsitat'
"""Парсим цитаты для дальнейшей отправки одной из них при использовании команды /say"""
response = requests.get(url=url, headers=headers)
soup = BeautifulSoup(response.text, 'lxml').find_all('p', class_='yl27R _10zjs', )
words_for_saying = []
for info in soup:
    info = info.find('span').text
    if info[0].isdigit():
        words_for_saying.append(info[info.find('.')+2:])

"""Создаем json-файл при его отсутствии. Следом считываем созданный/имеющийся json-файл, содержащий
    информацию о пользователях, в переменную data, чтобы после очередного обновления информации
    нужно было бы лишь перезаписать файл, не считывая повторно информацию из него"""
if not os.path.exists(config.file_path):
    with open(config.file_path, 'w', encoding='utf-8') as f:
        f.write('{}')
with open(config.file_path, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("I'm alive!")
    
    for guild in bot.guilds:
        for member in guild.members:
            """При включении бота он пробегает по всем участникам сервера на каждом сервере,
                к котором подключен. Если информация о пользователе в json-файле отсутствует
                и пользователь не является данным ботом, то информация о нем заносится в словарь
                data, который будет записан в файл после пробега по всем пользователям"""
            if data.get(str(member.id)) is None and member != bot.user:
                data[str(member.id)] = {
                    'Message_History': [],
                    'Additional_Info': 'Информация о пользователе отстутствует',
                    'Member_Activities': 'Информация отсутствует',
                    'Joined_At': str(member.joined_at)[:10] 
                }
    with open(config.file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))

@bot.tree.command(name='8ball', description='Задай свой вопрос магическому шару и получи на него ответ!')
async def ball(interaction: discord.Interaction, question: str):
    """Слэш-команда, позволяющая получить случайный ответ на вопрос, подразумевающий ответ да/нет"""
    answers = ["Бесспорно", "Предрешено", "Никаких сомнений", "Определённо да","Можешь быть уверен в этом",
               "Мне кажется - да", "Вероятнее всего", "Хорошие перспективы", "Знаки говорят - да", "Да",
               "Пока неясно, попробуй снова", "Спроси позже", "Лучше не рассказывать", "Сейчас нельзя предсказать",
               "Сконцентрируйся и спроси опять", "Даже не думай", "Мой ответ - нет", "По моим данным - нет", "Перспективы не очень хорошие", "Весьма сомнительно"]
    await interaction.response.send_message(f'Ответ на вопрос: "{question}" - {random.choice(answers)}')
    
@bot.tree.command(description='Используй данную команду, чтобы получить интересную цитату')
async def say(interaction: discord.Interaction):
    """Слэш-команда, позволяющая получить случайную цитату из сгенерированного ранее списка"""
    await interaction.response.send_message(random.choice(words_for_saying))
    
@bot.tree.command(description='Отправь анонимное сообщение через меня!')
async def direct(interaction: discord.Interaction, member: discord.Member, message: str):
    """Слэш-команда, позволяющая отправить анонимное сообщение с помощью бота"""
    await member.send(message)
    await interaction.response.send_message('Сообщение успешно отправлено!', ephemeral=True)
    
@bot.tree.command(description='Генератор рандомных чисел от 1 до limit')
async def numgen(interaction: discord.Interaction, limit: int):
    """Слэш-команда, генерирующая число в границах от 1 до указанной пользователем, включая их"""
    await interaction.response.send_message(f'Ваше число: {random.randint(1, limit)}')
    
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content.lower() == 'ping':
        await message.channel.send('Pong!')
        
    """Каждое сообщение, удовлетворяющее условиям ниже, записывается в текстовый файл, дробясь на слова.
        После такого сообщения случайным образом может сгенерироваться и отправиться сообщение,
        составленное из слов, хранящихся в файле. В случае упоминания бота пользователем,
        он отправляет пояснительное сообщение"""   
    if not message.content.startswith(config.PREFIX):
        if len(message.content) > 1:
            with open(config.text_file, 'a', encoding='utf-8') as f:
                print(*message.content.split(), file=f)
        
        if bot.user.mention in message.content:
            await message.reply('Привет! Мой создатель не научил меня толковой речи, но он всё ещё работает надо мной! Надеюсь, когда нибудь я смогу тебе ответить...')
        elif not random.randint(0, 100000) % 2:
            with open(config.text_file, 'r', encoding='utf-8') as f:
                text = f.read().split()
                to_send = ' '.join(random.choice(text) for _ in range(random.randint(1, 20)))
            await message.channel.send(to_send)
    
    """Обновляем историю сообщений пользователя"""
    data[str(message.author.id)]['Message_History'].append(message.content)
    with open(config.file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))
    
    await bot.process_commands(message)
    
@bot.event
async def on_member_join(member):
    """Приветсвуем пользователя на сервере кастомным приветствием, выдаем
        стартовую роль и создаем для него поле с информацией, после чего обновляем json-файл"""
    role = discord.utils.get(member.guild.roles, id=config.default_role_id)
    channel = bot.get_channel(config.lobby_channel_id)
    embed = discord.Embed(
        title='Новая пташка!',
        description=f'''Приветстуем, {member.name}!''',
        color=0xed952f
    )
    data[str(member.id)] = {
        'Message_History': [],
        'Additional_Info': 'Информация о пользователе отстутствует',
        'Member_Activities': 'Информация отсутствует',
        'Joined_At': str(member.joined_at)[:10] 
    }
    with open(config.file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))
    await member.add_roles(role)
    await channel.send(embed=embed)
    
@bot.event
async def on_command_error(ctx, error):
    """Проверка на несуществующую команду"""
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.reply(f'Данная команда у меня отсутствует, используйте {config.PREFIX}помощь, чтобы узнать список моих команд')
    else:
        print(error)
    
@bot.command(name='помощь')
async def help(ctx):
    """Позволяет получить навигацию по командам"""
    embed = discord.Embed(
        title="Команды бота",
        description=f'''{config.PREFIX}инфо *@mention* - информация о пользователе
                        {config.PREFIX}актив *активность*- изменение информации о своей активности
                        {config.PREFIX}доп.инфо *информация*- изменение дополнительной информации о себе
                        /8ball *ваш* *вопрос* - использование магического шара
                        /say - чтобы сгенерировать рандомную цитату
                        /direct - анонимное сообщение в личку
                        /numgen - генератор случайных чисел''',
        color=0x2fedc4
    )
    embed.set_thumbnail(url=config.picture)
    await ctx.send(embed=embed)

@bot.command(name="инфо")
async def info(ctx, member: discord.Member):
    """Позволяет пользователю получить информацию о другом пользователе"""
    if member == bot.user:
        await ctx.reply(random.choice(["Зачем тебе информация обо мне?", "Ты уверен, что хочешь что-то обо мне узнать?", f"Дополнительная информация по команде {config.PREFIX}помощь"]))
    else:
        embed = discord.Embed(
            title=f'Информация о пользователе {member.name}:',
            description=f"""Мои активности: {data[str(member.id)]['Member_Activities']}
                            Я пришел сюда: {data[str(member.id)]['Joined_At']}
                            Дополнительная информация: {data[str(member.id)]['Additional_Info']}"""
        )
        await ctx.reply(embed=embed)
@info.error
async def error(ctx, error):
    """Отправляем сообщение с пояснением в случае отсутствия аргумента"""
    err_embed = discord.Embed(
        title='Неправильное использование команды',
        description=f'''Правильное использование команды: {config.PREFIX}инфо *@упоминание*
                        Пример: {config.PREFIX}инфо *{bot.user.mention}*'''
        )
    await ctx.reply(embed=err_embed)
    
@bot.command(name='актив')
async def active(ctx, *, arg: str):
    """Заполняет поле 'Member_Activities' пользователя"""
    data[str(ctx.author.id)]['Member_Activities'] = arg
    with open(config.file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))
    await ctx.reply('Информация о вас обновлена!')
@active.error
async def error(ctx, error):
    """Отправляем сообщение с пояснением в случае отсутствия аргумента"""
    err_embed = discord.Embed(
        title='Неправильное использование команды',
        description=f'''Правильное использование команды: {config.PREFIX}актив *активность*
                        Пример: {config.PREFIX}актив *делаю бота, выполняю практику*'''
        )
    await ctx.reply(embed=err_embed)

@bot.command(name='доп.инфо')
async def add_info(ctx, *, arg: str):
    """Заполняет поле 'Additional_Info' пользователя"""
    data[str(ctx.author.id)]['Additional_Info'] = arg
    with open(config.file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))
    await ctx.reply('Информация о вас обновлена!')
@add_info.error
async def error(ctx, error):
    """Отправляем сообщение с пояснением в случае отсутствия аргумента"""
    err_embed = discord.Embed(
        title='Неправильное использование команды',
        description=f'''Правильное использование команды: {config.PREFIX}доп.инфо *информация*
                        Пример: {config.PREFIX}доп.инфо *По вопросам - в лс*'''
        )
    await ctx.reply(embed=err_embed)
    
@bot.command(name='чистка')
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=1_000_000):
    """Повзоляет администраторам чистить чат, в котором прописана команда"""
    await ctx.channel.purge(limit=amount)
    await ctx.channel.send('Очистка чата завершена')
@clear.error
async def error(ctx, error):
    """Отправляем сообщение в случае отсутствия прав администратора"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('У вас недостаточно прав!')

if __name__ == "__main__":
    bot.run(config.TOKEN)