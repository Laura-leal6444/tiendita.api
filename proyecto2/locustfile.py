### Autora: Laura Leal, tiendita; Proyecto 2: pruebas de carga con Locust

# Importamos de Locust: HttpUser (usuario virtual), task (marca las tareas), between (pausa al azar) y events (para avisar al terminar)
from locust import HttpUser, task, between, events

# Cuenta las respuestas de la compra para mostrar al final cuantas fueron exitosas (200) y cuantas rechazadas (400)
conteo_compras = {"200": 0, "400": 0, "otros": 0}


# Clase que representa a un cliente de la tiendita; Locust crea muchos clientes iguales a este al mismo tiempo
class UsuarioTienditaCompleto(HttpUser):
    # Intervalo aleatorio de descanso entre 0.2 y 0.8 segundos por usuario
    wait_time = between(0.2, 0.8)

    # POST comprar el Cafe (id 3): es la tarea con mas peso, asi simulamos la venta relampago (peso 5)
    @task(5)
    def comprarProducto(self):
        # catch_response=True nos deja decidir si la respuesta cuenta como exito o como falla
        with self.client.post("/productos/3", name="/productos/3 (comprar)", catch_response=True) as respuesta:
            if respuesta.status_code == 200:
                conteo_compras["200"] += 1
                respuesta.success()
            elif respuesta.status_code == 400:
                # El agotamiento de stock (400) es una respuesta correcta de negocio, no una falla del sistema
                conteo_compras["400"] += 1
                respuesta.success()
            else:
                conteo_compras["otros"] += 1
                respuesta.failure(f"Codigo inesperado: {respuesta.status_code}")

    # GET inicio: revisa que la API este viva (peso 1)
    @task(1)
    def getProducto(self):
        self.client.get("/")

    # FUNCION EXTRA: GET del Cafe (id 3) para ver su stock en tiempo real durante la prueba (peso 2)
    @task(2)
    def consultarStockCafe(self):
        self.client.get("/productos/3", name="/productos/3 (stock)")


# Al terminar la prueba imprime en la terminal el resumen de las compras
@events.test_stop.add_listener
def resumen_compras(environment, **kwargs):
    print("\n===== RESUMEN DE COMPRAS (POST /productos/3) =====")
    print(f"Compras exitosas (200): {conteo_compras['200']}")
    print(f"Compras rechazadas por falta de stock (400): {conteo_compras['400']}")
    print(f"Otros codigos: {conteo_compras['otros']}")
