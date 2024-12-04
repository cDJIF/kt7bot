from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import redis
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '7749397562:AAG02kTWgT7WFdCfWqmunICsrJhJyxTH7p4'
ADMIN_PASSWORD = '123'  
db = redis.Redis(host='localhost', port=6379, db=0)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class ProfileForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()


class ProfileUpdate(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()


def get_commands_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("/edit_profile", "/create_profile")
    keyboard.add("/export_profiles", "/delete")
    return keyboard

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я ваш телеграм-бот.", reply_markup=get_commands_keyboard())

@dp.message_handler(commands=['create_profile'], state='*')
async def create_profile(message: types.Message):
    await ProfileForm.waiting_for_name.set()
    await message.reply("Как вас зовут?")


@dp.message_handler(commands=['edit_profile'], state='*')
async def create_profile(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Имя"), KeyboardButton("Возраст"))
    await message.reply("Что бы Вы хотели изменить?", reply_markup=keyboard)
 
@dp.message_handler(lambda message: message.text in ["Имя", "Возраст"], state='*')
async def process_user_choice(message: types.Message):
    if message.text == "Имя":
        await ProfileUpdate.waiting_for_name.set()
        await message.reply("Как вас зовут?")     
    elif message.text == "Возраст":
        await ProfileUpdate.waiting_for_age.set()
        await message.reply("Сколько Вам лет?")


@dp.message_handler(state=ProfileUpdate.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        new_name = message.text
        print(new_name)
        user_keys = db.keys('user:*')
        
        user_found = False
        for user_key in user_keys:
            user_id = user_key.decode('utf-8').split(':')[1]
            if message.from_user.id == int(user_id):
                user_found = True
                user_data = db.hgetall(user_key)  
                current_username = user_data.get(b'username')
                current_full_name = user_data.get(b'full_name')
                
                try:
                    response = await update_user_on_backend(
                        user_id=message.from_user.id,
                        username=str(new_name),  
                        full_name=str(current_full_name.decode('utf-8')) 
                    )
                    print(response)
                    if "error" in response:
                        await message.reply(f"Ошибка при обновлении: {response['error']}")
                    else:
                        await message.reply(f"Профиль успешно обновлен! Новое имя: {new_name}")
                except Exception as e:
                    await message.reply(f"Произошла ошибка при отправке данных в backend: {e}")
                break
        
        if not user_found:
            await message.reply("Пользователь не найден.")
        
    await state.finish()


@dp.message_handler(state=ProfileUpdate.waiting_for_age)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        new_name = message.text
        print(new_name)
        user_keys = db.keys('user:*')
        
        user_found = False
        for user_key in user_keys:
            user_id = user_key.decode('utf-8').split(':')[1]
            if message.from_user.id == int(user_id):
                user_found = True
                user_data = db.hgetall(user_key)  
                current_username = user_data.get(b'username')
                current_full_name = user_data.get(b'full_name')
                
                try:
                    response = await update_user_on_backend(
                        user_id=message.from_user.id,
                        username=str(current_username.decode('utf-8')),  
                        full_name=str(new_name) 
                    )
                    print(response)
                    if "error" in response:
                        await message.reply(f"Ошибка при обновлении: {response['error']}")
                    else:
                        await message.reply(f"Профиль успешно обновлен! Новый возраст: {new_name}")
                except Exception as e:
                    await message.reply(f"Произошла ошибка при отправке данных в backend: {e}")
                break
        
        if not user_found:
            await message.reply("Пользователь не найден.")
        
    await state.finish()




@dp.message_handler(state=ProfileForm.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await ProfileForm.next()
    await message.reply("Сколько вам лет?")

class AdminDelete(StatesGroup):
    waiting_for_password = State()
    waiting_for_user_selection = State()


class AdminUpdate(StatesGroup):
    waiting_for_password = State()
    waiting_for_user_selection = State()
    waiting_for_field_selection = State()
    waiting_for_new_value = State()


@dp.message_handler(commands=['edit_user'], state='*')
async def delete_user_start(message: types.Message):
    await AdminUpdate.waiting_for_password.set()
    await message.reply("Введите пароль администратора:")


@dp.message_handler(commands=['delete_user'], state='*')
async def delete_user_start(message: types.Message):
    await AdminDelete.waiting_for_password.set()
    await message.reply("Введите пароль администратора:")


@dp.message_handler(state=AdminUpdate.waiting_for_password)
async def delete_user_password(message: types.Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await AdminUpdate.next()
        user_keys = db.keys('user:*')
        if user_keys:
            response = "Выберите номер пользователя для изменения:\n"
            for index, user_key in enumerate(user_keys, start=1):
                user_data = db.hgetall(user_key)
                user_id = user_key.decode('utf-8').split(':')[1]
                print(user_data)

                user_name = user_data.get(b'username')
                user_full = user_data.get(b'full_name')
                
                user_info = f"{index}. ID: {user_id}, Имя: {user_name.decode('utf-8')}, Age: {user_full.decode('utf-8')}\n"
                response += user_info

            await message.reply(response)
            await state.update_data(user_keys=[user_key.decode('utf-8') for user_key in user_keys])
            print(user_keys)
            await AdminUpdate.waiting_for_user_selection.set()


        else:
            await message.reply("Пользователи не найдены.")
            await state.finish()
    else:
        await message.reply("Неверный пароль администратора.")
        await state.finish()

NEED_ID = []
@dp.message_handler(state=AdminUpdate.waiting_for_user_selection)
async def select_field_to_edit(message: types.Message, state: FSMContext):
    user_keys = await state.get_data()
    user_id = user_keys['user_keys'][int(message.text) - 1].split(':')[1]
    await state.update_data(selected_user_id=user_id)
    NEED_ID.append(user_id)
    print("id: " , NEED_ID[len(NEED_ID)-1])
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("name"), KeyboardButton("age"))
    await message.reply("Что бы Вы хотели изменить?", reply_markup=keyboard)
    await AdminUpdate.waiting_for_field_selection.set()

@dp.message_handler(state=AdminUpdate.waiting_for_field_selection)
async def handle_field_selection(message: types.Message, state: FSMContext):
    selected_field = message.text.lower()
    await state.update_data(selected_field=selected_field)
    await message.reply(f"Введите новое значение для поля {selected_field}.")
    await AdminUpdate.waiting_for_new_value.set()


@dp.message_handler(state=AdminUpdate.waiting_for_new_value)
async def admin_update_field(message: types.Message, state: FSMContext, NEED_ID = NEED_ID):
    async with state.proxy() as data:
        new_value = message.text
        selected_user_id = NEED_ID[len(NEED_ID)-1]
        print("sel us id = " ,NEED_ID[len(NEED_ID)-1], selected_user_id)
        selected_field = data.get("selected_field")
        
        

            
        user_data = db.hgetall(selected_user_id)
        print(user_data)
        print(selected_field)
        current_username = user_data.get(b'username', b'').decode('utf-8')
        current_full_name = user_data.get(b'full_name', b'').decode('utf-8')

        try:
            if selected_field == "name":
                response = await update_user_on_backend(
                    user_id=int(selected_user_id),
                    username=new_value,
                    full_name=current_full_name
                )
            elif selected_field == "age":
                response = await update_user_on_backend(
                    user_id=int(selected_user_id),
                    username=current_username,
                    full_name=new_value
                )
            else:
                await message.reply("Некорректное поле для изменения.")
                return

            print(response)
            if "error" in response:
                await message.reply(f"Ошибка при обновлении: {response['error']}")
            else:
                await message.reply(
                    f"Данные пользователя успешно обновлены!\nПоле {selected_field} изменено на: {new_value}"
                )
        except Exception as e:
            await message.reply(f"Произошла ошибка при отправке данных в backend: {e}")
            

       

    await state.finish()


@dp.message_handler(state=AdminDelete.waiting_for_password)
async def delete_user_password(message: types.Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await AdminDelete.next()
        user_keys = db.keys('user:*')
        if user_keys:
            response = "Выберите номер пользователя для удаления:\n"
            for index, user_key in enumerate(user_keys, start=1):
                user_data = db.hgetall(user_key)
                user_id = user_key.decode('utf-8').split(':')[1]
                print(user_data)

                user_name = user_data.get(b'name') or user_data.get(b'full_name') or user_data.get(b'username')
                
                user_info = f"{index}. ID: {user_id}, Имя: {user_name.decode('utf-8')}\n"
                response += user_info

            await message.reply(response)
            await state.update_data(user_keys=[user_key.decode('utf-8') for user_key in user_keys])
            print(user_keys)
            await AdminDelete.waiting_for_user_selection.set()


        else:
            await message.reply("Пользователи не найдены.")
            await state.finish()
    else:
        await message.reply("Неверный пароль администратора.")
        await state.finish()


@dp.message_handler(commands=['delete_profile'], state='*')
async def delete_user_not_pass(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Да"), KeyboardButton("Нет"))
    await message.reply("Вы уверены в удалении профиля?", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text in ["Да", "Нет"], state='*')
async def process_user_choice(message: types.Message):
    if message.text == "Да":
        try:
            response = await delete_user_on_backend(message.from_user.id)
            if "error" in response:
                await message.reply(f"Ошибка: {response['error']}", reply_markup=types.ReplyKeyboardRemove())
            else:
                await message.reply("Ваш профиль был успешно удален.", reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            await message.reply(f"Ошибка: {e}", reply_markup=types.ReplyKeyboardRemove())
           
            
    elif message.text == "Нет":
        # Логика отмены действия
        await message.reply("Удаление профиля отменено.", reply_markup=types.ReplyKeyboardRemove())



@dp.message_handler(commands=['delete_user'], state='*')
async def delete_user_start(message: types.Message):
    await AdminDelete.waiting_for_password.set()
    await message.reply("Введите пароль администратора:")

@dp.message_handler(state=AdminDelete.waiting_for_user_selection)
async def delete_user_password(message: types.Message, state: FSMContext):
    print(1)
    user_keys = db.keys('user:*')
    #print(user_keys[int(message.text)-1].decode('utf-8').split(':')[1])
    user_id = (user_keys[int(message.text)-1].decode('utf-8').split(':')[1])
    try:
        response = await delete_user_on_backend(user_id)
        if "error" in response:
            await message.reply(f"Ошибка: {response['error']}")
        else:
            await message.reply("Пользователь успешно удален.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")
    await message.reply(response)
    await state.finish()


class AdminActions(StatesGroup):
    waiting_for_password = State()

@dp.message_handler(commands=['export_profiles'], state='*')
async def request_admin_password(message: types.Message):
    await AdminActions.waiting_for_password.set()
    await message.reply("Введите пароль администратора:")

@dp.message_handler(state=AdminActions.waiting_for_password)
async def process_admin_password(message: types.Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        try:
            user_keys = db.keys('user:*')
            if user_keys:
                response = "Список всех пользователей:\n"
                for user_key in user_keys:
                    user_data = db.hgetall(user_key)
                    user_id = user_key.decode('utf-8').split(':')[1]
                    print(user_data)
                    user_name = user_data.get(b'username')
                    user_age=user_data.get(b'full_name')
                    user_info = f"ID: {user_id}, Имя: {user_name.decode('utf-8')}, Возраст: {user_age.decode('utf-8')}\n"
                    response += user_info
                print(1)
                await message.reply(response)
            else:
                await message.reply("Пользователи не найдены.")
        except redis.RedisError as e:
            await message.reply(f"Произошла ошибка при получении данных: {e}")
        await state.finish()
    else:
        await message.reply("Неверный пароль администратора.")
        await state.finish()



@dp.message_handler(lambda message: message.text.isdigit(), state=ProfileForm.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['age'] = int(message.text)
        try:
            response = await create_user_on_backend(
                user_id=message.from_user.id,
                username=data['name'],
                full_name=str(data['age'])
            )
            if "error" in response:
                await message.reply(f"Ошибка: {response['error']}")
            else:
                await message.reply(f"Профиль успешно создан! Имя: {data['name']}, Возраст: {data['age']}")
        except Exception as e:
            await message.reply(f"Произошла ошибка при взаимодействии с backend: {e}")
    await state.finish()



import aiohttp

async def create_user_on_backend(user_id: int, username: str, full_name: str):
    async with aiohttp.ClientSession() as session:
        url = "http://127.0.0.1:8000/create"
        payload = {"user_id": user_id, "username": username, "full_name": full_name}
        async with session.post(url, json=payload) as response:
            return await response.json()

        

async def delete_user_on_backend(user_id: int):
    async with aiohttp.ClientSession() as session:
        url = f"http://127.0.0.1:8000/delete_user/{user_id}"
        async with session.delete(url) as response:
            return await response.json()
        

async def update_user_on_backend(user_id: int, username: str, full_name: str):
    async with aiohttp.ClientSession() as session:
        print(username,full_name)
        url = f"http://127.0.0.1:8000/update_user/{user_id}?username={username}&full_name={full_name}"
        async with session.put(url) as response:
            return await response.json()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)