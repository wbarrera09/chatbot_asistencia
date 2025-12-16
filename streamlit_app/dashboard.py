import sys
import os
import time
from datetime import datetime # ✅ Importado para manejo de fechas
import pytz # ✅ Importado para manejo de zonas horarias

# CONFIGURACIÓN DE RUTA
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from bot.db import get_connection

# Definimos la Zona Horaria de El Salvador
TZ_SV = pytz.timezone('America/El_Salvador')

# -------------------------------
# 1. CONFIGURACIÓN DE PÁGINA
# -------------------------------
st.set_page_config(
    page_title="CSDC Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# 2. CSS "MODERN BLUE" (Profesional y Corporativo)
# -------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Fuente Global */
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: #1e3a8a; /* Azul Noche Profundo */
    }

    /* Fondo */
    .stApp {
        background-color: #f8fafc; /* Gris/Azul muy pálido */
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* Tarjetas KPI (KPI Cards) */
    .kpi-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #bfdbfe; /* Borde azul cielo */
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.1); /* Sombra azul suave */
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
        border-color: #3b82f6;
    }

    .kpi-title {
        color: #2563eb; /* Azul Rey Vibrante */
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    
    .kpi-value {
        color: #0f172a; /* Azul casi negro */
        font-size: 1.5rem;
        font-weight: 800;
        margin: 0;
    }

    /* Contenedor de Insights */
    .insight-box {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px;
        height: 380px;
        overflow-y: auto;
        border: 1px solid #e2e8f0;
    }
    
    .insight-item {
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        background-color: #eff6ff; /* Azul muy claro */
        border-left: 4px solid #3b82f6; /* Borde Azul Brillante */
        font-size: 0.9rem;
        color: #1e40af; /* Texto Azul Fuerte */
    }
    
    .insight-item.warning {
        background-color: #fff1f2; /* Rojo muy claro para alertas */
        border-left-color: #f43f5e; 
        color: #881337;
    }
    
    .insight-item strong {
        display: block;
        margin-bottom: 4px;
        font-weight: 700;
    }

    /* Títulos */
    h1, h2, h3 {
        color: #172554; /* Azul Marino */
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 3. CARGA DE DATOS
# -------------------------------
def load_data():
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM requests ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Error DB: {e}")
        return pd.DataFrame()

df = load_data()


if not df.empty:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # Restamos 6 horas para ajustar la hora del servidor (UTC) a El Salvador
    df["timestamp"] = df["timestamp"] - pd.Timedelta(hours=6)

# -------------------------------
# 4. SIDEBAR (Código Modificado)
# -------------------------------
with st.sidebar:
    st.title("CSDC Analytics")
    st.markdown("Panel de Control")
    st.markdown("---")
    
    if not df.empty:
        min_date = df["timestamp"].min().date()
        max_date = df["timestamp"].max().date()
        
        date_range = st.date_input(
            "📅 Fechas:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    else:
        date_range = []

    st.markdown("###")
    
    # --- INICIO DEL TRUCO DE COLOR ---
    # Esto pinta el botón de un color específico (ej. Verde #10b981)
    st.markdown("""
        <style>
        /* Apunta a los botones dentro del sidebar */
        [data-testid="stSidebar"] .stButton > button {
            background-color: #0f172a; /* Azul Oscuro (puedes cambiarlo) */
            color: white;              /* Color del texto */
            border: 1px solid #1e293b; /* Borde sutil */
        }
        
        </style>
    """, unsafe_allow_html=True)
    # --- FIN DEL TRUCO ---

    if st.button("Actualizar", type="secondary", use_container_width=True):
        st.rerun()

# ---------------------------------------------------------
    # BOTÓN TELEGRAM: Minimalista (Solo Color Oficial)
    # ---------------------------------------------------------
    telegram_url = "https://web.telegram.org/k/#@CSDC_ASSISTANT_BOT"

    st.markdown(f"""
    <a href="{telegram_url}" target="_blank" style="text-decoration: none;">
        <div style="
            background-color: #24A1DE; 
            color: white;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: opacity 0.2s;
        " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
            Abrir chatbot en Telegram
        </div>
    </a>
    """, unsafe_allow_html=True)

# -------------------------------
# 5. LÓGICA
# -------------------------------
if df.empty:
    st.info("👋 Esperando datos...")
    st.stop()

if len(date_range) == 2:
    start, end = date_range
    mask = (df["timestamp"].dt.date >= start) & (df["timestamp"].dt.date <= end)
    df_filtered = df[mask]
else:
    df_filtered = df

df_filtered["date"] = df_filtered["timestamp"].dt.date
df_filtered["hour"] = df_filtered["timestamp"].dt.hour
dias_map = {0:"Lun", 1:"Mar", 2:"Mié", 3:"Jue", 4:"Vie", 5:"Sáb", 6:"Dom"}
df_filtered["day_name"] = df_filtered["timestamp"].dt.dayofweek.map(dias_map)

# -------------------------------
# 6. DASHBOARD VISUAL
# -------------------------------

# 
hora_actual_sv = datetime.now(TZ_SV).strftime('%d/%m/%Y %H:%M')

# Header
c1, c2 = st.columns([4, 1])
with c1:
    st.title("Resumen Operativo")
    st.markdown("Monitoreo de actividad en tiempo real.")
with c2:
    st.markdown(
        f"""
        <div style='text-align: right; padding-top: 20px; color: #000000; font-size:14px;'>
            Última actualización:<br><b>{hora_actual_sv}</b>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown("---")

# --- A. KPIs (Blue Style) ---
total = len(df_filtered)

# 
hoy = datetime.now(TZ_SV).date()
sol_hoy = len(df[df["timestamp"].dt.date == hoy])

if not df_filtered.empty:
    top_tramite = df_filtered["tipo_solicitud"].mode()[0]
    # Formateo bonito de hora pico
    hora_pico_val = df_filtered['hour'].mode()[0]
    hora_pico = f"{hora_pico_val:02d}:00"
else:
    top_tramite = "--"
    hora_pico = "--"

def kpi_card(title, value, icon):
    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{icon} {title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """

k1, k2, k3, k4 = st.columns(4)
k1.markdown(kpi_card("Total Casos", total, "📦"), unsafe_allow_html=True)
k2.markdown(kpi_card("Hoy", sol_hoy, "⚡"), unsafe_allow_html=True)
k3.markdown(kpi_card("Top Trámite", top_tramite, "🔥"), unsafe_allow_html=True)
k4.markdown(kpi_card("Hora Pico", hora_pico, "⏰"), unsafe_allow_html=True)

st.markdown("###")

# --- B. GRÁFICAS (Paleta Azul Ocean) ---
c_left, c_right = st.columns([2, 1])

# Paleta Oscura: Azul Medianoche -> Azul Rey -> Verde Petróleo
blue_palette = ['#172554', '#1e3a8a', '#1d4ed8', '#0e7490', '#155e75']

with c_left:
    st.subheader("📈 Tendencia")
    if not df_filtered.empty:
        trend = df_filtered.groupby("date").size().reset_index(name="count")
        
        fig_trend = px.area(
            trend, x="date", y="count", 
            template="plotly_white",
            height=380
        )
        # Color Principal: Azul Real (Royal Blue)
        fig_trend.update_traces(
            line_color="#090294", 
            fillcolor='rgba(37, 99, 235, 0.2)', 
            line_width=2
        )
        fig_trend.update_layout(
            xaxis_title=None, 
            yaxis_title=None, 
            margin=dict(t=20, b=20, l=20, r=20),
            hovermode="x unified"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

with c_right:
    st.subheader("📊 Distribución")
    if not df_filtered.empty:
        dist = df_filtered["tipo_solicitud"].value_counts()
        
        fig_pie = px.pie(
            values=dist.values, 
            names=dist.index, 
            hole=0.7,
            color_discrete_sequence=blue_palette # Aplicando paleta azul
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent')
        fig_pie.update_layout(
            showlegend=True, 
            legend=dict(orientation="h", y=-0.2),
            margin=dict(t=0, b=0, l=0, r=0),
            height=380
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# --- C. HEATMAP & INSIGHTS ---
st.markdown("###")
c_map, c_insights = st.columns([1, 1])

with c_map:
    st.subheader("🗓️ Intensidad Semanal")
    if not df_filtered.empty:
        heat = df_filtered.pivot_table(
            index="day_name", 
            columns="hour", 
            values="id", 
            aggfunc="count", 
            fill_value=0
        )
        order = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        heat = heat.reindex(order)
        
        fig_heat = px.imshow(
            heat,
            labels=dict(x="Hora", y="Día", color="Q"),
            color_continuous_scale="Blues", # Escala Azul
            aspect="auto",
            height=380
        )
        st.plotly_chart(fig_heat, use_container_width=True)

with c_insights:
    st.subheader("💡 Insights Automáticos")
    
    html_content = ""
    
    if not df_filtered.empty:
        pct_top = int((df_filtered["tipo_solicitud"].value_counts().max() / total) * 100)
        h_pico = df_filtered["hour"].mode()[0]
        
        # Tarjeta 1
        html_content += f"""<div class="insight-item"><strong>🔥 Patrón Dominante</strong>El {pct_top}% de las solicitudes son <b>'{top_tramite}'</b>.</div>"""
        
        # Tarjeta 2 (Warning - Se mantiene en rojo para resaltar alerta)
        if 8 <= h_pico <= 18:
            html_content += f"""<div class="insight-item warning"><strong>⚠️ Alerta de Tráfico</strong>Alta actividad detectada a las <b>{h_pico}:00 hrs</b>.</div>"""
        else:
            html_content += f"""<div class="insight-item"><strong>🌙 Actividad Nocturna</strong>Se detecta uso fuera de horario laboral ({h_pico}:00 hrs).</div>"""
            
        # Tarjeta 3
        html_content += f"""<div class="insight-item"><strong>✅ Rendimiento</strong>Se procesaron <b>{total}</b> casos exitosos.</div>"""
    
    else:
        html_content = "<div style='text-align:center; padding:20px; color:#6b7280;'>Sin datos suficientes.</div>"

    st.markdown(f"""
    <div class="insight-box">
        {html_content}
    </div>
    """, unsafe_allow_html=True)

# --- D. TABLA ---
st.markdown("###")
st.subheader("📋 Últimos Registros")
with st.expander("Ver tabla completa", expanded=True):
    st.dataframe(
        df_filtered[["timestamp", "nombre", "correo", "tipo_solicitud", "detalle"]],
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Fecha", format="DD MMM, HH:mm"),
            "tipo_solicitud": st.column_config.TextColumn("Tipo", width="medium"),
            "detalle": st.column_config.TextColumn("Detalle", width="large"),
        },
        use_container_width=True,
        hide_index=True
    )