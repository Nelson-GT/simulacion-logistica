import simpy
import math
import os
import google.generativeai as genai
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
    def __init__(self, env, capacidad, velocidad):
        self.env = env
        self.capacidad = capacidad
        self.carga_actual = capacidad
        self.velocidad = velocidad  # unidades de distancia por minuto
        self.ubicacion = (0, 0)     # Depósito inicial
        self.distancia_total = 0.0
        self.registro_entregas = []

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
        print(f"[{self.env.now:.2f} min] 🚚 Camión sale del depósito (0,0) con {self.carga_actual} unidades.")

        for cliente in ruta_clientes:
            # 1. Viaje hacia el cliente
            yield self.env.process(self.viajar(cliente.x, cliente.y))
            print(f"[{self.env.now:.2f} min] 📍 Llega al Cliente {cliente.id_cliente} en ({cliente.x}, {cliente.y}).")

            # 2. Proceso de entrega en el cliente (tiempo fijo de 15 minutos por descarga)
            tiempo_descarga = 15
            yield self.env.timeout(tiempo_descarga)

            if self.carga_actual >= cliente.demanda:
                self.carga_actual -= cliente.demanda
                self.registro_entregas.append(f"Cliente {cliente.id_cliente}: {cliente.demanda} uds")
                print(f"[{self.env.now:.2f} min] 📦 Entregadas {cliente.demanda} uds. Carga restante: {self.carga_actual}")
            else:
                print(f"[{self.env.now:.2f} min] ⚠️ Carga insuficiente para Cliente {cliente.id_cliente}. Faltan {cliente.demanda - self.carga_actual} uds.")

        # 3. Regreso al depósito
        yield self.env.process(self.viajar(0, 0))
        print(f"[{self.env.now:.2f} min] 🏠 Camión regresa al depósito.")

class AnalistaIA:
    """Se encarga de enviar los resultados de la simulación a un LLM para obtener conclusiones."""
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.disponible = False
            print("\n[IA] ⚠️ No se detectó GEMINI_API_KEY en el archivo .env. Omitiendo análisis de IA.")
        else:
            self.disponible = True
            genai.configure(api_key=api_key)
            self.modelo = genai.GenerativeModel('gemini-2.5-flash-lite')

    def generar_conclusion(self, distancia, tiempo, entregas):
        if not self.disponible:
            return "Análisis no disponible sin API Key."
        
        prompt = (
            f"Actúa como un experto en logística e investigación de operaciones. "
            f"Acabo de ejecutar una simulación de ruteo de vehículos (VRP). "
            f"Estos son los resultados finales del camión:\n"
            f"- Distancia total recorrida: {distancia:.2f} km\n"
            f"- Tiempo total de simulación: {tiempo:.2f} minutos\n"
            f"- Entregas realizadas: {entregas}\n\n"
            f"Basado en estos datos, redacta una breve conclusión (máximo 3 líneas) "
            f"y una recomendación técnica para optimizar la ruta en futuras simulaciones."
        )
        
        print("\n[IA] Consultando a la Inteligencia Artificial...")
        try:
            respuesta = self.modelo.generate_content(prompt)
            return respuesta.text
        except Exception as e:
            return f"Error al conectar con la API: {e}"

def principal():
    # 1. Preparar datos
    clientes = [
        Cliente(id_cliente=1, x=5, y=10, demanda=20),
        Cliente(id_cliente=2, x=15, y=12, demanda=15),
        Cliente(id_cliente=3, x=10, y=2, demanda=30),
        Cliente(id_cliente=4, x=2, y=8, demanda=10)
    ]

    # 2. Inicializar entorno SimPy
    env = simpy.Environment()
    camion = Camion(env, capacidad=100, velocidad=1.0) # 1.0 km por minuto (60 km/h)

    # 3. Asignar el proceso al entorno
    env.process(camion.realizar_ruta(clientes))

    # 4. Ejecutar simulación
    print("=== INICIO DE LA SIMULACIÓN LOGÍSTICA ===")
    env.run()
    
    # 5. Imprimir resultados locales
    print("\n=== RESULTADOS FINALES ===")
    print(f"Distancia total recorrida: {camion.distancia_total:.2f} unidades (km)")
    print(f"Tiempo total de simulación: {env.now:.2f} minutos")
    print(f"Registro de entregas: {', '.join(camion.registro_entregas)}")

    # 6. Integración con IA
    analista = AnalistaIA()
    analisis = analista.generar_conclusion(camion.distancia_total, env.now, camion.registro_entregas)
    print("\n=== CONCLUSIÓN Y RECOMENDACIÓN DE LA IA ===")
    print(analisis)

if __name__ == "__main__":
    principal()