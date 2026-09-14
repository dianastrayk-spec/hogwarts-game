import streamlit as st
from datetime import datetime

# ======================
# НАСТРОЙКИ СТРАНИЦЫ
# ======================
st.set_page_config(
    page_title="Квиддич Менеджер",
    page_icon="🧹",
    layout="wide"
)

st.title("🧹 Квиддич Менеджер")

# ======================
# ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ
# ======================
if "match_active" not in st.session_state:
    st.session_state.match_active = False
    st.session_state.round = 1
    st.session_state.score_a = 0
    st.session_state.score_b = 0
    st.session_state.possession = None          # "A" или "B"
    st.session_state.snitch_status = "Не появился"
    st.session_state.team_a = "Гриффиндор"
    st.session_state.team_b = "Слизерин"
    st.session_state.log = []
def calculate_round(roll_a, roll_b, roll_beater, roll_keeper, roll_seeker, round_num, possession, team_a, team_b):
    """
    roll_a - бросок охотников команды А
    roll_b - бросок охотников команды Б
    roll_beater - бросок загонщиков
    roll_keeper - бросок вратаря
    roll_seeker - бросок ловца
    """

    events = []
    score_a_add = 0
    score_b_add = 0
    new_possession = possession
    snitch_status = "Не появился"
    snitch_caught_by = None

    # ======================
    # 1. ОХОТНИКИ (определение владения и атаки)
    # ======================
    if possession is None:
        # Первый раунд — определяем инициативу
        if roll_a > roll_b:
            new_possession = "A"
            events.append(f"Инициативу захватывает {team_a}!")
        elif roll_b > roll_a:
            new_possession = "B"
            events.append(f"Инициативу захватывает {team_b}!")
        else:
            new_possession = "A" if round_num % 2 == 1 else "B"
            events.append("Ничья за инициативу! Владение получает команда по очереди.")
    else:
        new_possession = possession

    # Тексты событий охотников (по твоей таблице)
    chaser_events = {
        1: "Отличный пас, команда продвигается к воротам соперника",
        2: "Вратарь держит открытым кольцо, охотники мчатся к нему",
        3: "Красивый финт — перехват мяча у соперника",
        4: "Стандартные пасы. Публика требует зрелищ",
        5: "Слабый бросок — соперник перехватывает мяч",
        6: "Рискованный манёвр",
        7: "Бладжер летит на охотника! (внеплановый ход Загонщиков)",
        8: "Мощный удар почти через всё поле",
        9: "Командная комбинация",
        10: "Эпичный момент! Команда вырывается вперёд"
    }

    active_roll = roll_a if new_possession == "A" else roll_b
    events.append(chaser_events.get(active_roll, "Атака развивается"))

    # Смена владения при слабом броске
    if active_roll == 5:
        new_possession = "B" if new_possession == "A" else "A"
        events.append("Владение переходит к сопернику!")

    # ======================
    # 2. ЗАГОНЩИКИ
    # ======================
    beater_events = {
        1: "Бладжер бьёт по своему игроку!",
        2: "Фол! Назначается пенальти",
        3: "Неудачный удар — бладжер улетает в никуда",
        4: "Среднее отбитие — один охотник соперника нейтрализован (-1 в следующем раунде)",
        5: "Хороший удар — два охотника соперника нейтрализованы (-2 в следующем раунде)",
        6: "Удар по вратарю соперника! В следующем раунде возможен автоматический гол",
        7: "Бладжер выводит охотника соперника до конца игры",
        8: "Бладжер попал в загонщика соперника",
        9: "Двойной удар! Вратарь соперника выходит на 2 раунда, +20 очков",
        10: "Бладжер сбивает игрока соперника на 2 раунда"
    }
    events.append(f"Загонщики: {beater_events.get(roll_beater)}")

    # ======================
    # 3. ВРАТАРЬ
    # ======================
    # Гол происходит только если была атака (значения 2,6,8,9,10 у охотников)
    attack_values = [2, 6, 8, 9, 10]
    if active_roll in attack_values:
        keeper_events = {
            1: "Провал — ГОЛ!",
            2: "Мяч проскользнул — ГОЛ!",
            3: "Мяч проскользнул — ГОЛ!",
            4: "Отбил неуверенно, мяч у соперника",
            5: "Надёжный сейв, мяч уходит в аут",
            6: "Атака бладжером + бросок — сложная ситуация",
            7: "Красивый сейв! Толпа в восторге",
            8: "Героический прыжок! Дальний пас и ответная атака",
            9: "Героический прыжок! Ответный удар по воротам",
            10: "Легендарный сейв!"
        }
        events.append(f"Вратарь: {keeper_events.get(roll_keeper)}")

        if roll_keeper in [1, 2, 3]:
            if new_possession == "A":
                score_a_add += 10
            else:
                score_b_add += 10
            events.append("ГОЛ!")

    # ======================
    # 4. ЛОВЕЦ
    # ======================
    seeker_bonus = 3 if round_num >= 3 else 0
    final_seeker_roll = roll_seeker + seeker_bonus

    if final_seeker_roll <= 4:
        snitch_status = "Не появился"
        events.append("Снитч не видно")
    elif final_seeker_roll <= 6:
        snitch_status = "Появился — начало погони"
        events.append("Снитч появился! Ловцы начинают погоню")
    elif final_seeker_roll <= 9:
        snitch_status = "Опасная погоня"
        events.append("Снитч очень близко!")
    else:
        snitch_status = "Снитч пойман"
        # Упрощённо: пока пусть ловит команда, у которой владение
        snitch_caught_by = new_possession
        if new_possession == "A":
            score_a_add += 150
            events.append(f"Снитч пойман игроком {team_a}! +150 очков")
        else:
            score_b_add += 150
            events.append(f"Снитч пойман игроком {team_b}! +150 очков")

    # ======================
    # Итоговый текст
    # ======================
    result_text = f"### Раунд {round_num}\n\n"
    result_text += "\n".join([f"- {e}" for e in events])
    result_text += f"\n\n**Счёт раунда:** {team_a} +{score_a_add} | {team_b} +{score_b_add}"

    return {
        "text": result_text,
        "score_a": score_a_add,
        "score_b": score_b_add,
        "possession": new_possession,
        "snitch_status": snitch_status,
        "snitch_caught": snitch_caught_by is not None
    }

# ======================
# БОКОВАЯ ПАНЕЛЬ
# ======================
with st.sidebar:
    st.header("Управление матчем")

    # Список команд по умолчанию
    if "custom_teams" not in st.session_state:
        st.session_state.custom_teams = ["Гриффиндор", "Слизерин", "Когтевран", "Пуффендуй",
                                         "Дурмстранг", "Шармбатон", "Ильверморни"]

    # Поле для добавления новой команды
    with st.expander("Добавить свою команду"):
        new_team = st.text_input("Название новой команды")
        if st.button("Добавить команду"):
            if new_team and new_team not in st.session_state.custom_teams:
                st.session_state.custom_teams.append(new_team)
                st.success(f"Команда «{new_team}» добавлена!")
            elif new_team in st.session_state.custom_teams:
                st.warning("Такая команда уже есть")

    # Выбор команд
    team_a = st.selectbox("Команда А", st.session_state.custom_teams, index=0)
    team_b = st.selectbox("Команда Б", st.session_state.custom_teams, index=1)

    if st.button("Начать новый матч", type="primary"):
        st.session_state.match_active = True
        st.session_state.round = 1
        st.session_state.score_a = 0
        st.session_state.score_b = 0
        st.session_state.possession = None
        st.session_state.snitch_status = "Не появился"
        st.session_state.team_a = team_a
        st.session_state.team_b = team_b
        st.session_state.log = []
        st.success(f"Матч начат: {team_a} vs {team_b}") 

    st.divider()
    st.write(f"**Текущий матч:**")
    st.write(f"{st.session_state.team_a} vs {st.session_state.team_b}")
    st.write(f"Раунд: {st.session_state.round}")
    st.write(f"Счёт: {st.session_state.score_a} — {st.session_state.score_b}")
    st.write(f"Владение: {st.session_state.possession or 'Не определено'}")
    st.write(f"Снитч: {st.session_state.snitch_status}")

# ======================
# ОСНОВНАЯ ЧАСТЬ
# ======================
tab1, tab2, tab3 = st.tabs(["Матч", "Чемпионат", "Настройки"])

with tab1:
    if not st.session_state.match_active:
        st.info("Выбери команды и нажми «Начать новый матч» в боковой панели")
    else:
        st.subheader(f"Раунд {st.session_state.round}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Броски игроков")
            roll_chaser_a = st.number_input(
                f"Охотники {st.session_state.team_a} (1-10)", 
                min_value=1, max_value=10, value=5, key="chaser_a"
            )
            roll_chaser_b = st.number_input(
                f"Охотники {st.session_state.team_b} (1-10)", 
                min_value=1, max_value=10, value=5, key="chaser_b"
            )
            roll_beater = st.number_input(
                "Загонщики (1-10)", 
                min_value=1, max_value=10, value=5, key="beater"
            )
            roll_keeper = st.number_input(
                "Вратарь (1-10)", 
                min_value=1, max_value=10, value=5, key="keeper"
            )
            roll_seeker = st.number_input(
                "Ловец (1-10)", 
                min_value=1, max_value=10, value=5, key="seeker"
            )

        with col2:
            st.markdown("### Действия")
            if st.button("Рассчитать раунд", type="primary", use_container_width=True):
                result = calculate_round(
                    roll_a=roll_chaser_a,
                    roll_b=roll_chaser_b,
                    roll_beater=roll_beater,
                    roll_keeper=roll_keeper,
                    roll_seeker=roll_seeker,
                    round_num=st.session_state.round,
                    possession=st.session_state.possession,
                    team_a=st.session_state.team_a,
                    team_b=st.session_state.team_b
                )

                # Обновляем состояние матча
                st.session_state.score_a += result["score_a"]
                st.session_state.score_b += result["score_b"]
                st.session_state.possession = result["possession"]
                st.session_state.snitch_status = result["snitch_status"]
                st.session_state.log.append(result["text"])

                st.success("Раунд рассчитан!")
                st.rerun()


            if st.button("Следующий раунд", use_container_width=True):
                st.session_state.round += 1
                st.rerun()

            if st.button("Завершить матч", use_container_width=True):
                st.session_state.match_active = False
                st.success("Матч завершён")

        st.divider()
        st.subheader("История раундов")
        for entry in reversed(st.session_state.log):
            st.markdown(entry)
            st.markdown("---")

with tab2:
    st.subheader("Чемпионат и история матчей")

    # Инициализация списка матчей
    if "matches" not in st.session_state:
        st.session_state.matches = []

    # ----- Форма добавления матча -----
    with st.expander("Добавить прошедший матч", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            add_team_a = st.selectbox("Команда А", st.session_state.custom_teams, key="add_team_a")
            score_a = st.number_input("Очки команды А", min_value=0, value=0, step=10, key="add_score_a")

        with col2:
            add_team_b = st.selectbox("Команда Б", st.session_state.custom_teams, key="add_team_b")
            score_b = st.number_input("Очки команды Б", min_value=0, value=0, step=10, key="add_score_b")

        snitch = st.selectbox("Кто поймал снитч?", ["Никто", add_team_a, add_team_b], key="add_snitch")
        match_date = st.date_input("Дата матча")

        if st.button("Сохранить матч"):
            new_match = {
                "date": str(match_date),
                "team_a": add_team_a,
                "team_b": add_team_b,
                "score_a": score_a,
                "score_b": score_b,
                "snitch": snitch
            }
            st.session_state.matches.append(new_match)
            st.success("Матч добавлен!")
            st.rerun()

    st.divider()
    st.subheader("История матчей")

    if not st.session_state.matches:
        st.info("Пока нет сохранённых матчей")
    else:
        for i, match in enumerate(reversed(st.session_state.matches)):
            with st.container():
                st.markdown(
                    f"**{match['date']}**  \n"
                    f"{match['team_a']} {match['score_a']} — {match['score_b']} {match['team_b']}  \n"
                    f"Снитч: {match['snitch']}"
                )
               if st.button(f"Удалить матч", key=f"delete_{i}"):
                    # Удаляем из оригинального списка
                    real_index = len(st.session_state.matches) - 1 - i
                    st.session_state.matches.pop(real_index)
                    st.rerun()
                st.markdown("---")


with tab3:
    st.subheader("Настройки и таблицы событий")
    st.info("Здесь позже можно будет редактировать таблицы исходов")
