### Autora: Laura Leal, tiendita; Proyecto 2: Simulador de Venta Relampago (FastAPI y Locust)

# Importamos asyncio para el lock (cerrojo) y las esperas simuladas con await
import asyncio
# Importamos time y deque para el limitador de peticiones (se guardan los tiempos de las ultimas peticiones)
import time
from collections import deque
# Importamos FastAPI para crear la API, HTTPException para responder errores HTTP y status para los codigos
from fastapi import FastAPI, HTTPException, status
# Importamos CORS para permitir que el cliente (index.html) consuma la API
from fastapi.middleware.cors import CORSMiddleware
# Importamos JSONResponse para responder el error 429 del limitador
from fastapi.responses import JSONResponse
# Importamos BaseModel y Field de Pydantic v2 para validar los datos que llegan al crear un producto
from pydantic import BaseModel, Field

# Crea la aplicacion de FastAPI (la que ejecuta Uvicorn)
app = FastAPI(title="API Proyecto Tiendita")

# Cerrojo (lock) global: solo deja entrar a una peticion a la vez a la seccion critica de la compra
lock = asyncio.Lock()


# Limitador de peticiones del proyecto anterior (maximo 5 por segundo); se apaga en el Proyecto 2 para que Locust pueda mandar 100 usuarios
LIMITADOR_ACTIVO = False
LIMITE_PETICIONES = 5
VENTANA_SEGUNDOS = 1

# Guarda el momento en que llego cada una de las ultimas peticiones aceptadas
tiempos_peticiones = deque()
# Cerrojo propio del limitador (distinto al lock de la compra)
candado_limitador = asyncio.Lock()

# Middleware: se ejecuta en cada peticion antes de llegar al endpoint
@app.middleware("http")
async def limitar_peticiones(request, call_next):
    # Si el limitador esta apagado, deja pasar la peticion sin revisarla
    if not LIMITADOR_ACTIVO:
        return await call_next(request)
    async with candado_limitador:
        ahora = time.monotonic()
        # Quita las peticiones que ya pasaron hace 1 segundo o mas
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
    return await call_next(request)


# CORS: permite que el cliente en otro servidor (index.html) le hable a esta API sin que el navegador lo bloquee
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Modelo Pydantic para validar el producto que llega en el POST /productos
class ProductoNuevo(BaseModel):
    nombre: str = Field(min_length=1, description="Nombre del producto")
    precio: float = Field(gt=0, description="Precio del producto")
    cantidad: int = Field(ge=0, description="Cantidad disponible")


# Inventario de la tiendita: lista en memoria; el Cafe (id 3) empieza con stock = 1 para simular la contencion de la venta relampago
inventario = [
    {"id": 1, "nombre": "Coca-Cola", "precio": 20.0, "cantidad": 25},
    {"id": 2, "nombre": "Papas", "precio": 15.0, "cantidad": 40},
    {"id": 3, "nombre": "Café", "precio": 18.0, "cantidad": 1},  # Critico
    {"id": 4, "nombre": "Charcutería", "precio": 120.0, "cantidad": 10},
    {"id": 5, "nombre": "Vino rosado", "precio": 180.0, "cantidad": 12}
]

# Contador para que los ids sean autoincrementales (el siguiente id es el mayor que existe mas 1)
siguiente_id = max(p["id"] for p in inventario) + 1


# GET inicio: mensaje de bienvenida de la API
@app.get("/")
def home():
    return {"Message": "Hola bienvenido"}


# GET consulta los productos de mi inventario (async con await)
@app.get("/productos")
async def getProductos():
    await asyncio.sleep(0.05)  # simula la consulta a la base de datos, mientras espera el servidor atiende otras peticiones
    return inventario


# GET consulta un solo producto por su id; si no existe responde 404
@app.get("/productos/{producto_id}")
async def getProducto(producto_id: int):
    # Busca el producto por su id
    for producto in inventario:
        if producto["id"] == producto_id:
            return producto
    raise HTTPException(status_code=404, detail="Producto no encontrado")


# POST agrega un producto nuevo al inventario con id autoincremental (Pydantic valida los datos, si no cumplen responde 422)
@app.post("/productos", status_code=status.HTTP_201_CREATED)
async def addProducto(producto: ProductoNuevo):
    global siguiente_id
    await asyncio.sleep(0.05)  # simula guardar en la base de datos
    # Despues del await el id se toma y se aumenta sin ningun await en medio, asi dos peticiones nunca reciben el mismo id
    nuevo_producto = {
        "id": siguiente_id,
        "nombre": producto.nombre,
        "precio": producto.precio,
        "cantidad": producto.cantidad
    }
    siguiente_id += 1
    # Guarda el producto en el inventario
    inventario.append(nuevo_producto)
    return nuevo_producto


# DELETE borra un producto de mi inventario por su id (async sin await porque solo se busca en una lista en memoria)
@app.delete("/productos/{producto_id}")
async def deleteProducto(producto_id: int):
    # Busca el producto por su id y lo elimina si existe
    for producto in inventario:
        if producto["id"] == producto_id:
            inventario.remove(producto)
            return {"Message": "El producto fue eliminado"}
    return {"Message": "No fue encontrado el producto"}


# POST venta relampago: compra 1 unidad de un producto (SECCION CRITICA: modifica el inventario bajo concurrencia)
@app.post("/productos/{producto_id}")
async def comprar_producto(producto_id: int):
    try:
        # EXPERIMENTO B (con lock): deja activa la linea "async with lock:" y comentada la linea "if True:"
        # EXPERIMENTO A (sin lock): comenta la linea "async with lock:" y descomenta la linea "if True:"
        async with lock:  # Punto de control del experimento
        # if True:  # Experimento A (sin lock)
            # Busca el producto por su id
            for objeto in inventario:
                if objeto["id"] == producto_id:
                    # Revisa si todavia hay stock
                    if objeto["cantidad"] > 0:
                        await asyncio.sleep(0.05)  # Latencia simulada: abre la ventana de oportunidad para la condicion de carrera
                        # Descuenta 1 unidad del inventario
                        objeto["cantidad"] -= 1
                        return {"mensaje": "Producto comprado"}
                    else:
                        # Sin stock: error de negocio 400 (Bad Request)
                        raise HTTPException(400, "No hay stock")
            # Si el ciclo termino sin encontrarlo, tambien es error 400
            raise HTTPException(400, "Producto no existe")
    # Las HTTPException (errores 400 de negocio) se vuelven a lanzar para que no se conviertan en errores 500
    except HTTPException:
        raise
    # Cualquier otro error inesperado si es un error 500
    except Exception as error:
        raise HTTPException(500, f"Error interno: {str(error)}")
