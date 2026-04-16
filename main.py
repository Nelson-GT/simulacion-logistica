import simpy
import math
import os
from google import genai  # Actualizado al nuevo SDK
from dotenv import load_dotenv

# Cargar variables de entorno (API Key)
load_dotenv()

class Cliente:
    """Modela a un cliente con su ubicación geográfica y demanda de productos."""
    def __init__(self, id_cliente, x, y, demanda):
        self.id_cliente = id_cliente
        self.x = x
        self.y = y
        self.demanda = demanda

class Camion:
    """Modela el camión que realiza las entregas y lleva el registro de su recorrido."""
    def __init__(self, env, capacidad, velocidad, log_func, id_camion):
        self.env = env
        self.id_camion = id_camion
        self.capacidad = capacidad
        self.carga_actual = capacidad
        self.velocidad = velocidad  # unidades de distancia por minuto
        self.ubicacion = (0, 0)     # Depósito inicial
        self.distancia_total = 0.0
        self.registro_entregas = []
        self.log = log_func

    def viajar(self, destino_x, destino_y):
        """Simula el tiempo de viaje basado en la distancia euclidiana."""
        distancia = math.hypot(destino_x - self.ubicacion[0], destino_y - self.ubicacion[1])
        tiempo_viaje = distancia / self.velocidad
        
        # El generador simula que el camión está ocupado viajando
        yield self.env.timeout(tiempo_viaje)
        
        self.distancia_total += distancia
        self.ubicacion = (destino_x, destino_y)

    def realizar_ruta(self, ruta_clientes):
        """Proceso principal de SimPy: visita cada cliente en orden y regresa al depósito."""
        # Se unificó el print y el guardado en un solo llamado a self.log
        self.log(f"[{self.env.now:.2f} min] 🚚 Camión {self.id_camion} sale del depósito (0,0) con {self.carga_actual} unidades.")

        for cliente in ruta_clientes:
            # 1. Viaje hacia el cliente
            yield self.env.process(self.viajar(cliente.x, cliente.y))
            self.log(f"[{self.env.now:.2f} min] 📍 Camión {self.id_camion} llega al Cliente {cliente.id_cliente} en ({cliente.x}, {cliente.y}).")

            # 2. Proceso de entrega en el cliente (tiempo fijo de 15 minutos por descarga)
            tiempo_descarga = 15
            yield self.env.timeout(tiempo_descarga)

            if self.carga_actual >= cliente.demanda:
                self.carga_actual -= cliente.demanda
                self.registro_entregas.append(f"Cliente {cliente.id_cliente}: {cliente.demanda} uds")
                self.log(f"[{self.env.now:.2f} min] 📦 Camión {self.id_camion} entregó {cliente.demanda} uds. Carga restante: {self.carga_actual}")
            else:
                self.log(f"[{self.env.now:.2f} min] ⚠️ Camión {self.id_camion} no tiene carga suficiente para Cliente {cliente.id_cliente}. Faltan {cliente.demanda - self.carga_actual} uds.")

        # 3. Regreso al depósito
        yield self.env.process(self.viajar(0, 0))
        self.log(f"[{self.env.now:.2f} min] 🏠 Camión {self.id_camion} regresa al depósito.")

class AnalistaIA:
    """Se encarga de enviar los resultados de la simulación a un LLM para obtener conclusiones."""
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.disponible = False
            print("\n[IA] ⚠️ No se detectó GEMINI_API_KEY en el archivo .env. Omitiendo análisis de IA.")
        else:
            self.disponible = True
            self.client = genai.Client(api_key=api_key)

    def generar_conclusion(self, distancia, tiempo, entregas, contexto_completo):
        if not self.disponible:
            return "Análisis no disponible sin API Key."
        
        prompt = (
            f"Actúa como un Consultor Senior en Logística y Optimización de Procesos. "
            f"Analiza los resultados de esta simulación de transporte para la Facultad de Ingeniería.\n\n"
            f"INDICADORES CLAVE:\n"
            f"- Distancia: {distancia:.2f} km\n"
            f"- Tiempo Total: {tiempo:.2f} min\n"
            f"LOGS DETALLADOS DE LA OPERACIÓN:\n{contexto_completo}\n\n"
            f"TAREA: Proporciona un informe profesional que incluya:\n"
            f"1. Evaluación de la eficiencia de la ruta (Relación distancia/tiempo).\n"
            f"2. Análisis del cumplimiento de la demanda.\n"
            f"3. Una recomendación técnica avanzada (ej. Algoritmo de Ahorros de Clarke y Wright o Tabu Search) "
            f"para optimizar estos resultados específicos."
        )
        
        print("\n[IA] Consultando a la Inteligencia Artificial...")
        try:
            # Nuevo método de generación de contenido
            response = self.client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error al conectar con la API: {e}"

def principal():
    historial_logs = []
    
    # Se simplificó la función logger para que simplemente imprima y guarde
    def logger(mensaje):
        print(mensaje)
        historial_logs.append(mensaje)

    # --- Configuración de Clientes ---
    n_clientes = int(input("¿Cuántos clientes desea simular?: "))
    todos_los_clientes = []
    for i in range(n_clientes):
        print(f"\nDatos Cliente {i+1}:")
        x = float(input(f"  Coordenada X: "))
        y = float(input(f"  Coordenada Y: "))
        demanda = int(input(f"  Demanda: "))
        todos_los_clientes.append(Cliente(i+1, x, y, demanda))

    # --- Configuración de la Flota de Camiones ---
    n_camiones = int(input("\n¿Cuántos camiones tendrá la flota?: "))
    camiones = []
    env = simpy.Environment()

    for i in range(n_camiones):
        print(f"\nConfiguración Camión {i+1}:")
        v_kmh = float(input(f"  Velocidad (km/h): "))
        cap = int(input(f"  Capacidad de carga: "))
        
        # CORRECCIÓN: Se pasaron los parámetros por su nombre explícito (Keyword Arguments)
        nuevo_camion = Camion(
            env=env, 
            capacidad=cap, 
            velocidad=v_kmh/60, 
            log_func=logger, 
            id_camion=i+1
        )
        camiones.append(nuevo_camion)

        clientes_asignados = todos_los_clientes[i::n_camiones] 
        env.process(nuevo_camion.realizar_ruta(clientes_asignados))

    print("\n=== INICIANDO SIMULACIÓN DE FLOTA ===")
    env.run()

    # --- Consolidación de Resultados para la IA ---
    distancia_flota = sum(c.distancia_total for c in camiones)
    contexto_ia = "\n".join(historial_logs)
    
    analista = AnalistaIA()
    analisis = analista.generar_conclusion(distancia_flota, env.now, "Múltiples entregas", contexto_ia)
    
    print("\n" + "="*40)
    print("INFORME DE OPTIMIZACIÓN DE FLOTA (IA)")
    print("="*40)
    print(analisis)

if __name__ == "__main__":
    principal()