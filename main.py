### Autora: Laura Leal, 7 de octubre de 2026, tiendita; modificar inventario de productos, gestión de precios

# Importamos FastAPI para crear la API, HTTPException para responder errores como 404 o 409 y CORS para permitir que el cliente (index.html) la consuma
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Importamos asyncio para las funciones async con await (esperas simuladas)
import asyncio 
# Importamos time para medir los segundos, deque para guardar los tiempos de las peticiones y JSONResponse para responder el error 429
import time
from collections import deque
from fastapi.responses import JSONResponse

# Crea la aplicacion de FastAPI (la que ejecuta Uvicorn)
app = FastAPI()


# Limite de peticiones: maximo 5 por segundo (se define antes que CORS para que CORS quede por fuera y tambien cubra el error 429)
LIMITE_PETICIONES = 5
VENTANA_SEGUNDOS = 1

# Guarda el momento en que llego cada una de las ultimas peticiones aceptadas
tiempos_peticiones = deque()
# asyncio.Lock: hace que las peticiones revisen y modifiquen la lista de una en una, sin pisarse
candado = asyncio.Lock()

# Middleware: se ejecuta en cada peticion antes de llegar al endpoint
@app.middleware("http")
async def limitar_peticiones(request, call_next):
    # El candado solo protege la revision, no la peticion completa, para que las peticiones lentas no se bloqueen entre si
    async with candado:
        ahora = time.monotonic()
        # Quita de la lista las peticiones que ya pasaron hace 1 segundo o mas, esas ya no cuentan
        while tiempos_peticiones and ahora - tiempos_peticiones[0] >= VENTANA_SEGUNDOS:
            tiempos_peticiones.popleft()
        # Si ya hubo 5 peticiones en el ultimo segundo, rechaza esta con el error 429 (Too Many Requests)
        if len(tiempos_peticiones) >= LIMITE_PETICIONES:
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas peticiones, maximo 5 por segundo. Intenta de nuevo en un momento."},
                headers={"Retry-After": "1"}
            )
        # Si todavia hay espacio, registra esta peticion
        tiempos_peticiones.append(ahora)
    # Deja pasar la peticion hacia su endpoint y regresa la respuesta
    return await call_next(request)


# CORS: permite que el cliente en otro servidor (index.html) le hable a esta API sin que el navegador lo bloquee
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Inventario de la tiendita: lista en memoria que funciona como base de datos temporal
inventario = [
    {"id": 1, "nombre": "Coca-Cola", "precio": 20, "cantidad": 25},
    {"id": 2, "nombre": "Papas", "precio": 15, "cantidad": 40},
    {"id": 3, "nombre": "Café", "precio": 18, "cantidad": 15}
]

# GET inicio: mensaje de bienvenida de la API
@app.get("/")
def home():
    return {"Message": "Hola bienvenido"}

# GET consulta los productos de mi inventario (async con await)
@app.get("/productos")
async def getProductos():
    await asyncio.sleep(1)  # simula la consulta a la base de datos, mientras espera el servidor atiende otras peticiones
    return inventario

# POST agrega un producto nuevo a mi inventario (async con await)
@app.post("/productos")
async def addProducto(producto: dict):

    await asyncio.sleep(1)  # simula guardar en la base de datos (se espera antes de calcular el id para que no se repita)
# Calcula el id del producto nuevo
    nuevo_id = len(inventario) + 1
# Arma el producto con los datos que mando el cliente
    nuevo_producto = {
        "id": nuevo_id,    
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "cantidad": producto["cantidad"]
    }

# Guarda el producto en el inventario
    inventario.append(nuevo_producto)

    return inventario

# DELETE borra producto de mi inventario (async sin await)
@app.delete("/productos/{producto_id}")
async def deleteProducto(producto_id: int):
    # es async pero no lleva await porque aqui no hay nada que esperar, solo se busca en una lista en memoria
# Busca el producto por su id y lo elimina si existe
    for producto in inventario:
        if producto["id"] == producto_id:
            inventario.remove(producto)
            return {"Message": "El producto fue eliminado"}
    return {"Message": "No fue encontrado el producto"}


# Candado para que las compras se procesen de una en una y el stock del inventario no se descuadre
candado_compra = asyncio.Lock()

# POST comprar: compra 1 unidad de un producto y descuenta la cantidad del inventario (async con await)
@app.post("/productos/{producto_id}/comprar")
async def comprarProducto(producto_id: int):
    # async with candado: si llegan muchas compras al mismo tiempo, pasan una por una
    async with candado_compra:
        # Busca el producto por su id
        for producto in inventario:
            if producto["id"] == producto_id:
                # Si ya no hay unidades, responde el error 409 (Conflict)
                if producto["cantidad"] <= 0:
                    raise HTTPException(status_code=409, detail="Producto agotado")
                await asyncio.sleep(0.2)  # simula el cobro; sin el candado dos clientes podrian comprar la ultima unidad
                # Descuenta 1 unidad del inventario
                producto["cantidad"] -= 1
                return {"Message": "Compra realizada", "producto": producto["nombre"], "cantidad_restante": producto["cantidad"]}
    # Si el ciclo termino sin encontrarlo, responde el error 404 (Not Found)
    raise HTTPException(status_code=404, detail="Producto no encontrado")


# Prueba asyncio 5 segundos (espera con await y luego responde)
@app.get("/prueba-asyncio")
async def pruebaAsyncio():
    await asyncio.sleep(5)
    print("se terminaron los 5 segundos")
    return {"mensaje": "Prueba de asyncio terminada con éxito"}

#ejemplo de api get para obtener msj
@app.get("/")
def home():
    try:
        print("Hola")
        resultado = "1" + 1, 
        print("qué tranza?")
        return {"Message": "Hola bienvenido"}
    except Exception as error: 
        return {str(error)}





"""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio 

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


inventario = [
    {"id": 1, "nombre": "Coca-Cola", "precio": 20, "cantidad": 25},
    {"id": 2, "nombre": "Papas", "precio": 15, "cantidad": 40},
    {"id": 3, "nombre": "Café", "precio": 18, "cantidad": 15}
]

@app.get("/")
def home():
    return {"Message": "Hola bienvenido"}

@app.get("/productos")
def getProductos():
    return inventario

@app.post("/productos")
def addProducto(producto: dict):

    nuevo_id = len(inventario) + 1
    nuevo_producto = {
        "id": nuevo_id,    
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "cantidad": producto["cantidad"]
    }

    inventario.append(nuevo_producto)

    return inventario

@app.delete("/productos/{producto_id}")
def deleteProducto(producto_id: int):
    for producto in inventario:
        if producto["id"] == producto_id:
            inventario.remove(producto)
            return {"Message": "El producto fue eliminado"}
    return {"Message": "No fue encontrado el producto"}


import asyncio 

async def consultar_db():
   # cede el control al event loop 
    await asyncio.sleep(2)
    return {"status":"ok"}


#prueba asyncio
@app.get("/prueba-asyncii")
async def pruebaAsyncio():
    await asyncio.sleep(5)
    print("se terminaron los 5 segundos")"""