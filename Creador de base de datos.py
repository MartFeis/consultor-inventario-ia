import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# 1. Configuración del Motor Determinista
np.random.seed(42)
dias_simulacion = 365 * 3
fecha_inicio = datetime.now() - timedelta(days=dias_simulacion)

# 2. Generación del Catálogo de Productos (Tech)
categorias = ['GPU', 'Laptop', 'Monitor', 'Teclado Mecánico', 'SSD']
productos_data = []

for i in range(1, 51):
    categoria = np.random.choice(categorias)
    lead_time = np.random.randint(15, 45)
    costo = np.random.uniform(50, 1500)
    productos_data.append({
        'producto_id': i,
        'sku': f"{categoria[:3].upper()}-{1000+i}",
        'categoria': categoria,
        'lead_time_dias': lead_time,
        'costo_unitario': round(costo, 2),
        'stock_seguridad': np.random.randint(20, 100)
    })

df_productos = pd.DataFrame(productos_data)

# 3. Motor Cronológico de Transacciones y Quiebres
transacciones = []
estado_inventario = {p['producto_id']: {'stock': np.random.randint(100, 300), 'pedidos_pendientes': []} for p in productos_data}

fechas = [fecha_inicio + timedelta(days=d) for d in range(dias_simulacion)]

for fecha in fechas:
    for _, prod in df_productos.iterrows():
        pid = prod['producto_id']
        inv = estado_inventario[pid]
        
        # Procesar llegadas de pedidos (Compras)
        llegadas = [p for p in inv['pedidos_pendientes'] if p['fecha_llegada'] == fecha.date()]
        for llegada in llegadas:
            inv['stock'] += llegada['cantidad']
            transacciones.append({'producto_id': pid, 'tipo': 'COMPRA', 'cantidad': llegada['cantidad'], 'fecha': fecha.date()})
        inv['pedidos_pendientes'] = [p for p in inv['pedidos_pendientes'] if p['fecha_llegada'] > fecha.date()]
        
        # Simular Demanda Diaria (con picos estacionales aleatorios)
        demanda_base = int(np.random.normal(5, 2))
        demanda = max(0, demanda_base)
        
        if demanda > 0:
            if inv['stock'] >= demanda:
                inv['stock'] -= demanda
                transacciones.append({'producto_id': pid, 'tipo': 'VENTA', 'cantidad': -demanda, 'fecha': fecha.date()})
            else:
                # Quiebre de stock (Stockout)
                if inv['stock'] > 0:
                    transacciones.append({'producto_id': pid, 'tipo': 'VENTA', 'cantidad': -inv['stock'], 'fecha': fecha.date()})
                    inv['stock'] = 0
                transacciones.append({'producto_id': pid, 'tipo': 'QUIEBRE_STOCK', 'cantidad': demanda, 'fecha': fecha.date()})
                
        # Lógica de Reposición (Punto de Reorden)
        en_transito = sum(p['cantidad'] for p in inv['pedidos_pendientes'])
        if (inv['stock'] + en_transito) < prod['stock_seguridad']:
            cantidad_pedido = prod['stock_seguridad'] * 3
            fecha_llegada = fecha.date() + timedelta(days=prod['lead_time_dias'])
            inv['pedidos_pendientes'].append({'cantidad': cantidad_pedido, 'fecha_llegada': fecha_llegada})

df_transacciones = pd.DataFrame(transacciones)

# 4. Generar Snapshot del Inventario Actual
inventario_actual = []
for pid, data in estado_inventario.items():
    inventario_actual.append({
        'producto_id': pid,
        'stock_disponible': data['stock'],
        'fecha_ultima_auditoria': fechas[-1].date()
    })
df_inventario = pd.DataFrame(inventario_actual)

# 5. Exportación a Base de Datos Local
engine = create_engine('sqlite:///inventario_tech.db')
df_productos.to_sql('productos', engine, index=False, if_exists='replace')
df_transacciones.to_sql('transacciones_stock', engine, index=False, if_exists='replace')
df_inventario.to_sql('inventario_actual', engine, index=False, if_exists='replace')

print(f"Base de datos generada exitosamente. Total transacciones: {len(df_transacciones)}")