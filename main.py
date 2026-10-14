### Autora: Laura Leal, 7 de octubre de 2026, tiendita; modificar inventario de productos, gestión de precios

from fastapi import FastAPI
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
async def getProductos():
    await asyncio.sleep(1)  # simula la consulta a la base de datos, mientras espera el servidor atiende otras peticiones
    return inventario

@app.post("/productos")
async def addProducto(producto: dict):

    await asyncio.sleep(1)  # simula guardar en la base de datos (se espera antes de calcular el id para que no se repita)
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
async def deleteProducto(producto_id: int):
    # es async pero no lleva await porque aqui no hay nada que esperar, solo se busca en una lista en memoria
    for producto in inventario:
        if producto["id"] == producto_id:
            inventario.remove(producto)
            return {"Message": "El producto fue eliminado"}
    return {"Message": "No fue encontrado el producto"}


# Prueba asyncio
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