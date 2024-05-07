let carrito = [];

function añadirAlCarrito(nombre, precio) {
  const cantidadSeleccionada = document.querySelector('.producto[data-nombre="' + nombre + '"] .cantidad select').value;

  const productoExistente = carrito.find(producto => producto.nombre === nombre);

  if (productoExistente) {
    productoExistente.cantidad += parseInt(cantidadSeleccionada);
  } else {
    carrito.push({ nombre, precio, cantidad: parseInt(cantidadSeleccionada) });
  }

  actualizarContadorCarrito();
  actualizarListaCarrito();

  localStorage.setItem('carrito', JSON.stringify(carrito));
}



function actualizarContadorCarrito() {
  const contadorCarrito = document.getElementById('contadorCarrito');
  contadorCarrito.textContent = carrito.reduce((total, producto) => total + (producto.cantidad || 1), 0);
}

function mostrarDetalles(nombre, precio) {
  console.log(`Detalles de ${nombre}. Precio: $${precio}`);
}

function actualizarListaCarrito() {
  const listaCarritoSidebar = document.getElementById('listaCarritoSidebar');
  const totalCarritoSidebar = document.getElementById('totalCarritoSidebar');
  const finalizarCompraSidebar = document.getElementById('finalizarCompraSidebar');

  listaCarritoSidebar.innerHTML = '';

  let totalCarrito = 0;
  carrito.forEach(producto => {
      const listItem = document.createElement('li');
      const iconoBasura = document.createElement('img');
      iconoBasura.src = 'https://grafica-rima.github.io/Imagenes/basura.jpg';
      iconoBasura.alt = 'Eliminar';
      iconoBasura.classList.add('eliminar-producto');

      iconoBasura.dataset.nombre = producto.nombre;

      iconoBasura.addEventListener('click', function() {
          const nombreProducto = this.dataset.nombre;
          eliminarProducto(nombreProducto);
      });

      listItem.appendChild(iconoBasura);

      const contenidoProducto = `${producto.nombre} x${producto.cantidad} - $${producto.precio * (producto.cantidad || 1)}`;
      listItem.appendChild(document.createTextNode(contenidoProducto));

      listaCarritoSidebar.appendChild(listItem);

      totalCarrito += producto.precio * (producto.cantidad || 1);
  });

  totalCarritoSidebar.textContent = `$${totalCarrito.toFixed(2)}`;

  // Mostrar u ocultar el botón "Finalizar Compra" según la cantidad de productos en el carrito
  finalizarCompraSidebar.style.display = carrito.length > 0 ? 'block' : 'none';
}


function eliminarProducto(nombre) {
  carrito = carrito.filter(producto => producto.nombre !== nombre);
  actualizarContadorCarrito();
  actualizarListaCarrito();
}

function agregarEventoEliminarProducto() {
  const iconosBasura = document.querySelectorAll('.eliminar-producto');
  iconosBasura.forEach(icono => {
    icono.addEventListener('click', function() {
      const nombreProducto = this.dataset.nombre;
      eliminarProducto(nombreProducto);
    });
  });
}

function mostrarCarrito() {
  document.getElementById("sidebar").style.display = "block";
}

function ocultarCarrito() {
  document.getElementById("sidebar").style.display = "none";
}

function subirArchivo() {
  const inputArchivo = document.getElementById('#archivoInput');

  if (archivoInput.files.length === 0) {
    alert("Cargue un archivo para enviar.");
  } else {
    alert("Su archivo se ha cargado correctamente. Envíe un mensaje desde el formulario de contacto para ponernos en contacto.");
  }
}

let cantidadAnterior = 0;

function ajustarCantidad(nombre, cambio) {
  const productoExistente = carrito.find(producto => producto.nombre === nombre);
  if (productoExistente) {
    productoExistente.cantidad = Math.max((productoExistente.cantidad || 0) + cambio, 0);
    actualizarListaCarrito();
    actualizarContadores();
  }
}

function actualizarContadores() {
  const productosConSelector = document.querySelectorAll('.producto .cantidad select');

  productosConSelector.forEach(selector => {
    const nombreProducto = selector.closest('.producto').dataset.nombre;
    const productoExistente = carrito.find(producto => producto.nombre === nombreProducto);

    if (productoExistente) {
      productoExistente.cantidad = parseInt(selector.value);
    }
  });

  actualizarListaCarrito();
}

const productosConSelector = document.querySelectorAll('.producto .cantidad select');

productosConSelector.forEach(selector => {
  selector.addEventListener('change', () => {
    const nombreProducto = selector.closest('.producto').dataset.nombre;
    ajustarCantidad(nombreProducto, selector.value - cantidadAnterior);
    cantidadAnterior = selector.value;
  });
});


document.addEventListener("DOMContentLoaded", function () {
  window.addEventListener("scroll", function () {
    let scrollPosition = window.scrollY;
    let windowHeight = window.innerHeight;
    let documentHeight = document.body.offsetHeight;
    let triggerPoint = documentHeight - windowHeight - 10;

    if (scrollPosition > triggerPoint) {
      document.querySelector(".container-footer").style.display = "block";
    } else {
      document.querySelector(".container-footer").style.display = "none";
    }
  });
});


function mostrarModal() {
  let modal = document.getElementById("myModal");
  modal.style.display = "block";
}

function cerrarModal() {
  let modal = document.getElementById("myModal");
  modal.style.display = "none";
}

document.querySelector('a[href="#nosotros"]').addEventListener('click', function(event) {
  event.preventDefault();
  mostrarModal();
});

function mostrarModalTrabaja() {
  let modal = document.getElementById("modalTrabaja");
  modal.style.display = "block";
}

function cerrarModalTrabaja() {
  let modal = document.getElementById("modalTrabaja");
  modal.style.display = "none";
}

document.querySelector('a[href="#trabaja-con-nosotros"]').addEventListener('click', function(event) {
  event.preventDefault();
  mostrarModalTrabaja();
});

function mostrarModalPrivacidad() {
  let modal = document.getElementById("modalPrivacidad");
  modal.style.display = "block";
}

function cerrarModalPrivacidad() {
  let modal = document.getElementById("modalPrivacidad");
  modal.style.display = "none";
}

document.querySelector('a[href="#privacidad"]').addEventListener('click', function(event) {
  event.preventDefault();
  mostrarModalPrivacidad();
});

const btn = document.getElementById('button');

document.getElementById('form')
 .addEventListener('submit', function(event) {
   event.preventDefault();

   btn.value = 'Enviando...';

   const serviceID = 'default_service';
   const templateID = 'template_ah8n5jh';

   emailjs.sendForm(serviceID, templateID, this)
    .then(() => {
      btn.value = 'Enviar correo';
      alert('Correo enviado');
    }, (err) => {
      btn.value = 'Enviar correo';
      alert(JSON.stringify(err));
    });
});

function inicializarBusqueda() {
  const input = document.getElementById('searchInput');
  input.addEventListener('input', buscar);
}

function buscar() {
  const input = document.getElementById('searchInput');
  const searchTerm = input.value.trim().toLowerCase(); // Obtener el término de búsqueda en minúsculas, eliminando espacios en blanco al inicio y al final

  const productos = document.querySelectorAll('.producto');
  productos.forEach(producto => {
    const nombre = producto.dataset.nombre.toLowerCase(); // Obtener el nombre del producto en minúsculas
    if (nombre.includes(searchTerm)) {
      producto.style.display = 'block'; // Mostrar el producto si coincide con el término de búsqueda
    } else {
      producto.style.display = 'none'; // Ocultar el producto si no coincide con el término de búsqueda
    }
  });

  // También puedes ocultar los encabezados h2 u otros elementos aquí
  const encabezados = document.querySelectorAll('h2'); // Ajusta el selector según los elementos que desees ocultar/mostrar
  encabezados.forEach(encabezado => {
    encabezado.style.display = searchTerm ? 'none' : 'block'; // Si hay un término de búsqueda, oculta los encabezados, de lo contrario, muéstralos
  });
}

document.addEventListener('DOMContentLoaded', inicializarBusqueda);
