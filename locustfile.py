### Autora: Laura Leal, tiendita; prueba de carga con Locust

# Importamos de Locust: HttpUser (usuario virtual que hace peticiones HTTP), task (marca las tareas) y between (pausa al azar)
from locust import HttpUser, task, between
# Importamos random para escoger productos al azar
import random


# Clase que representa a un cliente de la tiendita; Locust crea muchos clientes iguales a este al mismo tiempo
class ClienteTiendita(HttpUser):
    # Cada cliente espera entre 0.5 y 1.5 segundos despues de cada tarea, como una persona real
    wait_time = between(0.5, 1.5)

    # Funcion que revisa la respuesta: 200, 201 y 409 (producto agotado) son normales; el 429 se marca como fallo para ver cuando actua el limite de 5 por segundo
    def revisar(self, respuesta):
        if respuesta.status_code in (200, 201, 409):
            respuesta.success()
        elif respuesta.status_code == 429:
            respuesta.failure("429 Demasiadas peticiones (limite de 5 por segundo)")
        else:
            respuesta.failure(f"Codigo inesperado: {respuesta.status_code}")

    # GET inicio: mensaje de bienvenida (peso 1, la menos frecuente)
    @task(1)
    def inicio(self):
        with self.client.get("/", catch_response=True) as respuesta:
            self.revisar(respuesta)

    # GET productos: consulta el inventario (peso 3, la mas frecuente)
    @task(3)
    def ver_productos(self):
        with self.client.get("/productos", catch_response=True) as respuesta:
            self.revisar(respuesta)

    # POST producto: agrega un producto nuevo al inventario (peso 1)
    @task(1)
    def agregar_producto(self):
        producto = {"nombre": "Bohemia", "precio": random.randint(10, 50), "cantidad": random.randint(1, 30)}
        with self.client.post("/productos", json=producto, catch_response=True) as respuesta:
            self.revisar(respuesta)

    # DELETE producto: borra un producto al azar; name agrupa todos los ids en una sola linea de resultados (peso 1)
    @task(1)
    def eliminar_producto(self):
        id_producto = random.randint(4, 30)
        with self.client.delete(f"/productos/{id_producto}", name="/productos/{id}", catch_response=True) as respuesta:
            self.revisar(respuesta)

    # POST comprar: compra 1 unidad de un producto al azar y descuenta el inventario; cuando se agota responde 409 (peso 2)
    @task(2)
    def comprar_producto(self):
        id_producto = random.randint(1, 3)
        with self.client.post(f"/productos/{id_producto}/comprar", name="/productos/{id}/comprar", catch_response=True) as respuesta:
            self.revisar(respuesta)
