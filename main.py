import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from io import StringIO

st.set_page_config(page_title="🧭 Анализ CSV-файла (Streamlit)", layout="wide")
st.title("🧭 Анализ CSV-файла")

# Инициализация df и filename в состояние сессии
if 'df' not in st.session_state:
    st.session_state.df = None
if 'filename' not in st.session_state:
    st.session_state.filename = None

# Открытие файла
upload_file = st.file_uploader(
    "Откройте файл в формате CSV",
    type=["csv"],
    help="Можно открыть файл с разделителям в формате CSV с кодировкой UTF-8 или Windows-1251"
)

if upload_file is not None:
    try:
        # Получение содержимого файла
        content = upload_file.getvalue()

        # Декодирование UTF-8
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            # Декодирование Windows-1251
            text = content.decode('cp1251')

        # Чтение данных из файла CSV, разделитель определяется автоматически
        df = pd.read_csv(StringIO(text), sep=None, engine='python')

        # Сохранение данных в session_state
        st.session_state.df = df
        st.session_state.filename = upload_file.name

        st.success(
            f"Файл **'{upload_file.name}'** открыт, данные загружены "
            f"Размер файла: {df.shape[0]:,} строк × {df.shape[1]} столбцов"
        )

    except Exception as e:
        st.error(f"Ошибка открытия файла: {str(e)}")

# Получаем данные из session_state
df = st.session_state.df
if df is not None:
    # Вывод содержимого файла
    st.subheader("🗺️ Содержимое файла:")
    st.dataframe(df, use_container_width=True, height=300)

    # Выбор столбцов
    st.subheader("📋️ Отображаемые столбцы")
    all_cols = df.columns.tolist()

    selected_cols = st.multiselect(
        "Выберите необходимые столбцы",
        options=all_cols,
        default=all_cols[:min(6, len(all_cols))],
        key="selected_cols"
    )

    if selected_cols:
        st.dataframe(df[selected_cols], use_container_width=True)

    # Определение типов столбцов
    def get_column_type(series):
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        else:
            try:
                pd.to_datetime(series.dropna().head(10))
                return "datetime"
            except:
                return "text"

    # Словарь типов столбцов
    col_types = {col: get_column_type(df[col]) for col in df.columns}
    numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
    datetime_cols = [c for c, t in col_types.items() if t == "datetime"]

    # Статистический анализ
    st.subheader("📝 Статистический анализ")

    if numeric_cols:
        stats_col = st.selectbox(
            "Выберите столбец для статистического анализа",
            options=numeric_cols,
            key="stats_col"
        )

        if stats_col:
            col_data = pd.to_numeric(df[stats_col], errors='coerce').dropna()

            if len(col_data) > 0:
                mean = col_data.mean()
                median = col_data.median()
                std = col_data.std()

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Количество", len(col_data))
                col2.metric("Среднее", f"{mean:.4f}")
                col3.metric("Медиана", f"{median:.4f}")
                col4.metric("Среднеквадратичное отклонение", f"{std:.4f}")

                # Гистограмма распределения значений
                st.markdown("**Гисторграмма распределения значений**")
                hist_data = pd.DataFrame({
                    stats_col: col_data
                })
                hist_chart = alt.Chart(hist_data).mark_bar().encode(
                    alt.X(f'{stats_col}:Q', bin=alt.Bin(maxbins=20), title='Интервалы значений'),
                    alt.Y('count()', title='Количество записей')
                ).properties(title=f"Гистограмма: {stats_col}")
                st.altair_chart(hist_chart, use_container_width=True)
            else:
                st.warning("Ошибка: отсутствуют числовые значения")
    else:
        st.info("В файле нет данных с числами для статистического анализа")

    # Визуализация
    st.subheader("📊 Визуализация данных")

    chart_type = st.radio(
        "Тип графика",
        ["Линейный", "Диаграмма рассеяния", "Столбчатая диаграмма"],
        horizontal=True,
        key="chart_type"
    )

    x_options = all_cols
    y_options = numeric_cols if numeric_cols else all_cols

    col_x, col_y = st.columns(2)
    with col_x:
        x_col = st.selectbox("Ось X", options=x_options, key="x_col")
    with col_y:
        y_col = st.selectbox("Ось Y", options=y_options, key="y_col")

    if x_col and y_col:
        chart_df = df[[x_col, y_col]].copy()

        if col_types[x_col] == "datetime":
            chart_df[x_col] = pd.to_datetime(chart_df[x_col], errors='coerce')

        chart_df = chart_df.dropna()

        if len(chart_df) > 0:
            if chart_type == "Линейный":
                chart = alt.Chart(chart_df).mark_line(point=True).encode(
                    x=alt.X(x_col, title=x_col),
                    y=alt.Y(y_col, title=y_col),
                    tooltip=[x_col, y_col]
                ).properties(title=f"{y_col} vs {x_col} (линейный график)")
            elif chart_type == "Диаграмма рассеяния":
                chart = alt.Chart(chart_df).mark_circle(size=60).encode(
                    x=alt.X(x_col, title=x_col),
                    y=alt.Y(y_col, title=y_col),
                    tooltip=[x_col, y_col]
                ).properties(title=f"{y_col} vs {x_col} (диаграмма рассеяния)")
            else:
                chart = alt.Chart(chart_df).mark_bar().encode(
                    x=alt.X(x_col, title=x_col),
                    y=alt.Y(y_col, title=y_col, aggregate='mean'),
                    tooltip=[x_col, y_col]
                ).properties(title=f"Среднее {y_col} по {x_col} (столбчатая диаграмма)")

            st.altair_chart(chart, use_container_width=True)

            # Сохранение данных в файл
            csv_download = chart_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💼 Сохранить данные в файл CSV",
                data=csv_download,
                file_name=f"chart_data_{x_col}_{y_col}.csv",
                mime="text/csv"
            )
        else:
            st.warning("Ошибка: нет данных для построения графика")
else:
    st.info("📂 Откройте файл с данными в формате CSV для анализа")