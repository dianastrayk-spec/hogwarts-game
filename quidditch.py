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
    st.session_state.bludger_control = None    # "A", "B" или None
    st.session_state.active_effects = []       # список активных эффектов
    st.session_state.log = []
    st.session_state.extra_rolls = []
    st.session_state.effects = {
        "chaser_penalty": {"A": 0, "B": 0},
        "auto_goal": None,
        "Keeper_out": {"A": 0, "B": 0},
        "chaser_out": {"A": False, "B": False},
        "temp_out": {"A": 0, "B": 0}
    }
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

    if new_possession == "A":
        hitting_side = "A"
        target_side = "B"
        hitting_team = team_a
        target_team = team_b
    elif new_possession == "B":
        hitting_side = "B"
        target_side = "A"
        hitting_team = team_b
        target_team = team_a
    else:
        hitting_side = "A"
        target_side = "B"
        hitting_team = team_a
        target_team = team_b

    new_effects = []
    effects = st.session_state.get("effects", {
        "chaser_penalty": {"A": 0, "B": 0},
        "auto_goal": None,
        "keeper_out": {"A": 0, "B": 0},
        "chaser_out": {"A": False, "B": False},
        "temp_out": {"A": 0, "B": 0},
        "seeker_out": {"A": 0, "B": 0}
    })

    if roll_beater == 1:
        events.append(f"Загонщики {hitting_team}: Бладжер бьёт по своему игроку!")

    elif roll_beater == 2:
        events.append(f"Загонщики {hitting_team}: Фол! Назначается пенальти")

    elif roll_beater == 3:
        events.append(f"Загонщики {hitting_team}: Неудачный удар - бладжер улетает в никуда")
   
    elif roll_beater == 4:
       events.append (f"Загонщики {hitting_team}: Среднее отбитие — один охотник {target_team} нейтрализован (-1 в следующем раунде)")
       effects["chase_penalty"][target_side] = 1
       new_effects.append(f"Охотники {target_team}: - 1  в следующем раунде")

    elif roll_beater == 5:
       events.append (f"Загонщики {hitting_team}: Хороший удар — два охотника {target_team} нейтрализован (-2 в следующем раунде)")
       effects["chase_penalty"][target_side] = 2
       new_effects.append(f"Охотники {target_team}: - 2  в следующем раунде")

    elif roll_beater == 6:
       events.append (f"Загонщики {hitting_team}: Удар по вратарю {target_team}! Автоматический гол")
       effects["auto_goal"] = hitting_side
       new_effects.append(f"Автогол для {hitting_team}: следующем раунде")
      
    elif roll_beater == 7:
       events.append (f"Загонщики {hitting_team}: Вывел охотника команды {target_team} до конца игры!")
       effects["chaser_out"][target_side] = True
       new_effects.append(f"Охотник {target_team} выведен до конца матча")    

    elif roll_beater == 8:
       events.append (f"Загонщики {hitting_team}: Бладжер попал в загонщика {target_team}")

    elif roll_beater == 9:
        events.append (f"Загонщики {hitting_team}: Двойной удар! Вратарь {target_team} выходит на 2 раунда")
        effects["keeper_out"][target_side] = 2
        if hitting_side == "A":
            score_a_add += 20
        else:
            score_b_add += 20
        events.append(f"+20 очков команде {hitting_team} за двойной удар!")
        new_effects.append(f"Вратарь {target_team} вне игры на 2 раунда")

    elif roll_beater == 10:
         events.append (f"Загонщики {hitting_team}: Бладжер сбивает ловца {target_team} на 2 раунда!")
         effects["seeker_out"][target_side] = 2
         new_effects.append(f"Ловец {target_team} выведен на 2 раунда")

    else:
        events.append (f"Загонщики {hitting_team}: Неизвестный результат ({roll_beater})")
    }

    if new_possession == "A":
        hitting_team = team_a
        target_team = team_b
        target_side = "B"
    elif new_possession == "B":
        hitting_team = team_a
        target_team = team_b
        target_side = "A"
    else:
        hitting_team = team_a
        target_team = team_b
        target_side = "B"
        
    events.append(f"Загонщики: {beater_events.get(roll_beater)}")

    new_effects = []

    if roll_beater == 7:
        events [-1] = f"Загонщики {hitting_team} вывел охотника команды {target_team} до конца игры!"
        new_effects.append(f"Охотник {target_team} выведен до конца матча")

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
    # 4. ЛОВЕЦ (обновление)
    # ======================
    final_seeker_roll = roll_seeker

    # В первые 3 раунда снитч поймать нельзя
    if round_num <= 3:
        if final_seeker_roll <= 6:
            snitch_status = "Не появился"
            events.append("Снитч не видно.")
        elif final_seeker_roll <= 7:
            snitch_status = "Появился - начало погони"
            events.append("Снитч появился! Ловцы начинают погоню.")
        elif final_seeker_roll <= 9:
            snitch_status = "Опасная погоня"
            events.append("Опасная погоня! Снитч очень близко.")
        else: # 10-13
            snitch_status = "Почти пойман"
            events.append("Снитч почти в руках! Нужен дополнительный бросок Ловца.")
    else:
        # С 4-го раунда полноценная логика
        if final_seeker_roll <= 4:
            snitch_status = "Не появился"
            events.append("Снитч не видно.")
        
        elif final_seeker_roll <= 6:
            snitch_status = "Появился — начало погони"
            events.append("Снитч появился! Ловцы начинают погоню.")
        
        elif final_seeker_roll <= 8:
            snitch_status = "Опасная погоня"
            events.append("Опасная погоня! Снитч очень близко, ловцы идут почти плечом к плечу.")
        
        elif final_seeker_roll == 9:
            snitch_status = "Попытка поимки"
            events.append("Снитч почти в руках! Нужен дополнительный бросок на поимку.")

    # ======================
    # Обработка дополнительных бросков
    # ======================
    if st.session_state.get("extra_rolls"):
        events.append("--- Дополнительные броски ---")
        
        for extra in st.session_state.extra_rolls:
            pos = extra["position"]
            val = extra["value"]
            check = extra["check_type"]
            
        if pos == "Ловец":
            if val <= 4:
                events.append(f"Ловец ({val}): Снитч ускользнул! Погоня начинается заново.")
                snitch_status = "Ускользнул"
                
            elif val <= 8:
                events.append(f"Ловец ({val}): Снитч быстро поймал соперник!")
                # Соперник получает +150
                if new_possession == "A":
                    score_b_add += 150
                    events.append(f"Снитч пойман командой {team_b}! +150")
                else:
                    score_a_add += 150
                    events.append(f"Снитч пойман командой {team_a}! +150")
                snitch_status = "Пойман соперником"
                
            elif val <= 10:
                events.append(f"Ловец ({val}): Погоня на равных! Нужен дополнительный бросок Чёт/Нечет, чтобы определить победителя.")
                snitch_status = "Погоня на равных"
                
            else:  # 11–13
                events.append(f"Ловец ({val}): Снитч стопроцентно пойман!")
                if new_possession == "A":
                    score_a_add += 150
                    events.append(f"Снитч пойман командой {team_a}! +150")
                else:
                    score_b_add += 150
                    events.append(f"Снитч пойман командой {team_b}! +150")
                snitch_status = "Пойман"

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
        "snitch_caught": snitch_caught_by is not None,
        "new_effects": new_effects
        "effects": effects
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
        st.session_state.effects = {
        "chaser_penalty": {"A": 0, "B": 0},
        "auto_goal": None,
        "Keeper_out": {"A": 0, "B": 0},
        "chaser_out": {"A": False, "B": False},
        "temp_out": {"A": 0, "B": 0}
    }

    st.divider()
    st.write("**Текущий матч:**")
    st.write(f"{st.session_state.team_a} vs {st.session_state.team_b}")
    st.write(f"**Раунд:** {st.session_state.round}")
    st.write(f"**Счёт:** {st.session_state.score_a} — {st.session_state.score_b}")
    
    # Статус владения
    quaffle = st.session_state.possession
    if quaffle == "A":
        st.write(f"**Квоффл:** {st.session_state.team_a}")
    elif quaffle == "B":
        st.write(f"**Квоффл:** {st.session_state.team_b}")
    else:
        st.write("**Квоффл:** Не определён")

    # Бладжеры
    bludger = st.session_state.get("bludger_control")
    if bludger == "A":
        st.write(f"**Бладжеры:** {st.session_state.team_a}")
    elif bludger == "B":
        st.write(f"**Бладжеры:** {st.session_state.team_b}")
    else:
        st.write("**Бладжеры:** Свободны")

    st.write(f"**Снитч:** {st.session_state.snitch_status}")

    # Активные эффекты
    if st.session_state.get("active_effects"):
        st.write("**Активные эффекты:**")
        for effect in st.session_state.active_effects:
            st.write(f"- {effect}")

    if st.session_state.get("show_download"):
        st.download_button(
            label="Скачать результат последнего матча",
            data=st.session_state.last_match_csv,
            file_name=st.session_state.last_match_name,
            mime="text/csv"
        )
        if st.button("Скрыть кнопку скачивания"):
            st.session_state.show_download = False
            st.rerun()

# ======================
# ОСНОВНАЯ ЧАСТЬ
# ======================
tab1, tab2, tab3 = st.tabs(["Матч", "Чемпионат", "Настройки"])

with tab1:
    if not st.session_state.match_active:
        st.info("Выбери команды и нажми «Начать новый матч» в боковой панели")
    else:
        st.subheader(f"Раунд {st.session_state.round}")

        # Быстрый статус
        status_col1, status_col2, status_col3 = st.columns(3)
        with status_col1:
            q = st.session_state.possession
            q_text = st.session_state.team_a if q == "A" else st.session_state.team_b if q == "B" else "—"
            st.info(f"**Квоффл:** {q_text}")
        with status_col2:
            b = st.session_state.get("bludger_control")
            b_text = st.session_state.team_a if b == "A" else st.session_state.team_b if b == "B" else "Свободны"
            st.info(f"**Бладжеры:** {b_text}")
        with status_col3:
            st.info(f"**Снитч:** {st.session_state.snitch_status}")


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
                "Ловец (1-13)", 
                min_value=1, max_value=13, value=5, key="seeker"
            )
            
        st.markdown("---")
        st.subheader("Дополнительные броски")

        if st.button("+ Добавить бросок"):
            st.session_state.extra_rolls.append({
                "position": "Загонщик",
                "check_type": "Попал / Не попал",
                "value": 5
            })
            st.rerun()

        positions = ["Ловец", "Охотник", "Загонщик", "Вратарь"]
        check_types = [
            "Попал / Не попал", 
            "Чёт / Нечет", 
            "По таблице позиции",
            "Просто значение"
        ]

        for i, roll in enumerate(st.session_state.extra_rolls):
            st.markdown(f"**Бросок {i+1}**")
            cols = st.columns([2.5, 3, 2, 1])

            with cols[0]:
                st.session_state.extra_rolls[i]["position"] = st.selectbox(
                    "Позиция",
                    positions,
                    index=positions.index(roll.get("position", "Загонщик")),
                    key=f"extra_pos_{i}"
                )

            with cols[1]:
                st.session_state.extra_rolls[i]["check_type"] = st.selectbox(
                    "Тип проверки",
                    check_types,
                    index=check_types.index(roll.get("check_type", "Попал / Не попал")),
                    key=f"extra_type_{i}"
                )

            with cols[2]:
                st.session_state.extra_rolls[i]["value"] = st.number_input(
                    "Результат",
                    min_value=1,
                    max_value=13,
                    value=roll.get("value", 5),
                    key=f"extra_val_{i}"
                )

            with cols[3]:
                st.write("")  # для выравнивания
                st.write("")
                if st.button("Удалить", key=f"del_extra_{i}"):
                    st.session_state.extra_rolls.pop(i)
                    st.rerun()

            st.markdown("---")

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

                if "effects" in result:
                    st.session_state.effects = result["effects"]

                if "new_effects" in result and result["new_effects"]:
                    if "active_effects" not in st.session_state:
                        st.session_state.active_effects = []
                    for effect in result["new_effects"]:
                        if effect not in st.session_state.active_effects:
                            st.session_state.active_effects.append(effect)

                st.success("Раунд рассчитан!")
                st.rerun()


            if st.button("Следующий раунд", use_container_width=True):
                st.session_state.round += 1
                st.rerun()

            if st.button("Завершить матч", use_container_width=True):
                # Определяем, кто поймал снитч
                if st.session_state.score_a > st.session_state.score_b:
                    snitch_winner = st.session_state.team_a
                elif st.session_state.score_b > st.session_state.score_a:
                    snitch_winner = st.session_state.team_b
                else:
                    snitch_winner = "Никто"

                # Создаём запись о матче
                final_match = {
                    "date": str(datetime.now().date()),
                    "team_a": st.session_state.team_a,
                    "team_b": st.session_state.team_b,
                    "score_a": st.session_state.score_a,
                    "score_b": st.session_state.score_b,
                    "snitch": snitch_winner
                }

                # Сохраняем в историю
                if "matches" not in st.session_state:
                    st.session_state.matches = []
    
                st.session_state.matches.append(final_match)

                import pandas as pd

                # Сохраняем данные для скачивания
                st.session_state.last_match_csv = pd.DataFrame([final_match]).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.session_state.last_match_name = f"{st.session_state.team_a}_vs_{st.session_state.team_b}.csv"
                st.session_state.show_download = True

                # Сбрасываем матч
                st.session_state.match_active = False
                st.session_state.round = 1
                st.session_state.score_a = 0
                st.session_state.score_b = 0
                st.session_state.possession = None
                st.session_state.snitch_status = "Не появился"
                st.session_state.bludger_control = None
                st.session_state.active_effects = []
                st.session_state.log = []
            
                st.success("Матч завершён и сохранён в историю!")
                st.rerun()

            st.divider()
            st.subheader("История раундов")
            if st.session_state.log:
                for entry in reversed(st.session_state.log):
                    st.markdown(entry)
                    st.markdown("---")
            else:
                st.info ("История раундов пока пуста")
                
with tab2:
    st.subheader("Чемпионат и история матчей")

    # Инициализация
    if "matches" not in st.session_state:
        st.session_state.matches = []

    # ===== Загрузка матчей из файла =====
    st.markdown("### Загрузить историю матчей")
    uploaded_file = st.file_uploader("Загрузить CSV с матчами", type=["csv"])

    if uploaded_file is not None:
        try:
            import pandas as pd
            df_uploaded = pd.read_csv(uploaded_file)
            st.session_state.matches = df_uploaded.to_dict("records")
            st.success(f"Загружено матчей: {len(st.session_state.matches)}")
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка при загрузке файла: {e}")

    # ===== Добавление матча вручную =====
    with st.expander("Добавить прошедший матч вручную"):
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
                "score_a": int(score_a),
                "score_b": int(score_b),
                "snitch": snitch
            }
            st.session_state.matches.append(new_match)
            st.success("Матч добавлен!")
            st.rerun()

    st.divider()

    # ===== История матчей =====
    st.subheader("История матчей")

    if not st.session_state.matches:
        st.info("Пока нет сохранённых матчей")
    else:
        for i, match in enumerate(reversed(st.session_state.matches)):
            st.markdown(
                f"**{match['date']}**  \n"
                f"{match['team_a']} {match['score_a']} — {match['score_b']} {match['team_b']}  \n"
                f"Снитч: {match['snitch']}"
            )
            if st.button("Удалить матч", key=f"delete_{i}"):
                real_index = len(st.session_state.matches) - 1 - i
                st.session_state.matches.pop(real_index)
                st.rerun()
            st.markdown("---")

    # ===== Турнирная таблица =====
    st.divider()
    st.subheader("Турнирная таблица")

    if st.session_state.matches:
        stats = {}

        for match in st.session_state.matches:
            for team in [match["team_a"], match["team_b"]]:
                if team not in stats:
                    stats[team] = {"Игры": 0, "Победы": 0, "Поражения": 0, "Очки": 0, "Снитчи": 0}

            stats[match["team_a"]]["Игры"] += 1
            stats[match["team_b"]]["Игры"] += 1
            stats[match["team_a"]]["Очки"] += match["score_a"]
            stats[match["team_b"]]["Очки"] += match["score_b"]

            if match["score_a"] > match["score_b"]:
                stats[match["team_a"]]["Победы"] += 1
                stats[match["team_b"]]["Поражения"] += 1
            elif match["score_b"] > match["score_a"]:
                stats[match["team_b"]]["Победы"] += 1
                stats[match["team_a"]]["Поражения"] += 1

            if match["snitch"] == match["team_a"]:
                stats[match["team_a"]]["Снитчи"] += 1
            elif match["snitch"] == match["team_b"]:
                stats[match["team_b"]]["Снитчи"] += 1

        import pandas as pd
        df = pd.DataFrame.from_dict(stats, orient="index")
        df = df.sort_values(by=["Очки", "Победы", "Снитчи"], ascending=False)
        st.dataframe(df, use_container_width=True)

        leader = df.index[0]
        st.success(f"Сейчас лидирует: **{leader}** с {int(df.loc[leader, 'Очки'])} очками")

        # Кнопка скачать турнирную таблицу
        csv_table = df.to_csv(index=True, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="Скачать турнирную таблицу (CSV)",
            data=csv_table,
            file_name="quidditch_standings.csv",
            mime="text/csv"
        )

    else:
        st.info("Нет данных для таблицы")

    # ===== Выгрузка =====
    st.divider()
    st.subheader("Выгрузка данных")

    if st.session_state.matches:
        import pandas as pd
        df_matches = pd.DataFrame(st.session_state.matches)
        csv_matches = df_matches.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

        st.download_button(
            label="Скачать все матчи (CSV)",
            data=csv_matches,
            file_name="quidditch_matches.csv",
            mime="text/csv"
        )

            
# ----- Турнирная таблица -----
st.divider()
st.subheader("Турнирная таблица")

if st.session_state.matches:
    stats = {}

    for match in st.session_state.matches:
        for team in [match["team_a"], match["team_b"]]:
             if team not in stats:
                stats[team] = {
                    "Игры": 0, 
                    "Победы": 0, 
                    "Поражения": 0,        # сумма всех набранных очков 
                    "Очки": 0,        # сумма всех набранных очков 
                    "Снитчи": 0}
 
        stats[match["team_a"]]["Игры"] += 1
        stats[match["team_b"]]["Игры"] += 1

            # Добавляем реальные очки, набранные в матче
        stats[match["team_a"]]["Очки"] += match["score_a"]
        stats[match["team_b"]]["Очки"] += match["score_b"]

            # Победы и поражения
        if match["score_a"] > match["score_b"]:
            stats[match["team_a"]]["Победы"] += 1
            stats[match["team_b"]]["Поражения"] += 1
        elif match["score_b"] > match["score_a"]:
            stats[match["team_b"]]["Победы"] += 1
            stats[match["team_a"]]["Поражения"] += 1

            # Снитчи
        if match["snitch"] == match["team_a"]:
             stats[match["team_a"]]["Снитчи"] += 1
        elif match["snitch"] == match["team_b"]:
            stats[match["team_b"]]["Снитчи"] += 1

    import pandas as pd
    df = pd.DataFrame.from_dict(stats, orient="index")
    df = df.sort_values(by=["Очки", "Победы", "Снитчи"], ascending=False)
    st.dataframe(df, use_container_width=True)

    # Победитель
    leader = df.index[0]
    st.success(f"Сейчас лидирует: **{leader}** с {df.loc[leader, 'Очки']} очками")
else:
    st.info("Нет данных для таблицы")

with tab3:
    st.subheader("Настройки и таблицы событий")
    st.info("Здесь позже можно будет редактировать таблицы исходов")
