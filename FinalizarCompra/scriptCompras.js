const radioEnvioDomicilio = document.getElementById('envioDomicilio');
const radioPuntoEntrega = document.getElementById('puntoEntrega');
const campoDomicilio = document.getElementById('puntoEntregaDomicilio');
const inputDomicilio = document.getElementById('domicilioPuntoEntrega');
const botonGuardar = document.getElementById('guardarDomicilio');

let ultimaSeleccion = null;
let metodoEnvioSeleccionado = false;

radioEnvioDomicilio.addEventListener('change', function() {
  if (this.checked) {
    ultimaSeleccion = 'envioDomicilio';
    campoDomicilio.style.display = 'none'; // Asegúrate de ocultar el campo de domicilio si cambia a "Envío a domicilio"
    metodoEnvioSeleccionado = true;
  }
});

radioPuntoEntrega.addEventListener('change', function() {
  if (this.checked) {
    ultimaSeleccion = 'puntoEntrega';
    campoDomicilio.style.display = 'block';
    metodoEnvioSeleccionado = true;
  }
});

botonGuardar.addEventListener('click', function() {
  // Si no se ha seleccionado ninguna opción, muestra un mensaje y retorna false
  if (ultimaSeleccion === null) {
    alert('Por favor, selecciona una opción antes de guardar.');
    return false;
  }

  // Obtener el valor del campo de domicilio
  const domicilioValue = inputDomicilio.value.trim();

  // Validar que se haya ingresado un domicilio si la última opción fue "Punto de entrega"
  if (ultimaSeleccion === 'puntoEntrega' && domicilioValue === '') {
    alert('Por favor, ingresa un domicilio válido.');
    return false;
  }

  const formatoDomicilio = /^[A-Za-z\s]+ \d+, [A-Za-z\s]+$/;
  if (!formatoDomicilio.test(domicilioValue)) {
    alert('El formato del domicilio no es válido. Ejemplo válido: "Nombre de calle" "123" "," "Localidad".');
    return false;
  }

  // Puedes realizar otras validaciones aquí según tus necesidades

  // Si se llega hasta aquí, el formulario es válido y puedes proceder con el guardado
  alert('Domicilio guardado: ' + domicilioValue);
  return true;

  metodoEnvioSeleccionado = true;

});


// Manejar el evento beforeunload para mostrar la advertencia
window.addEventListener('beforeunload', function(e) {
  // Verificar si se ha seleccionado un método de envío
  if (!metodoEnvioSeleccionado) {
    const mensaje = 'Seleccione un método de envío antes de salir de la página. ¿Está seguro de que desea salir?';
    e.returnValue = mensaje; // Estándar antiguo
    return mensaje; // Estándar actual
  }
});

function mostrarModal() {
  let modal = document.getElementById("myModal");
  modal.style.display = "block";
}

// Función para cerrar el modal
function cerrarModal() {
  let modal = document.getElementById("myModal");
  modal.style.display = "none";
}

// Mostrar el modal cuando se hace clic en el enlace "Nosotros"
document.querySelector('a[href="#nosotros"]').addEventListener('click', function(event) {
  event.preventDefault();
  mostrarModal();
});

function mostrarModalTrabaja() {
  let modal = document.getElementById("modalTrabaja");
  modal.style.display = "block";
}

// Función para cerrar el modal
function cerrarModalTrabaja() {
  let modal = document.getElementById("modalTrabaja");
  modal.style.display = "none";
}

// Mostrar el modal cuando se hace clic en el enlace "Nosotros"
document.querySelector('a[href="#trabaja-con-nosotros"]').addEventListener('click', function(event) {
  event.preventDefault();
  mostrarModalTrabaja();
});

function mostrarModalPrivacidad() {
  let modal = document.getElementById("modalPrivacidad");
  modal.style.display = "block";
}

// Función para cerrar el modal
function cerrarModalPrivacidad() {
  let modal = document.getElementById("modalPrivacidad");
  modal.style.display = "none";
}

// Mostrar el modal cuando se hace clic en el enlace "Nosotros"
document.querySelector('a[href="#privacidad"]').addEventListener('click', function(event) {
  event.preventDefault();
  mostrarModalPrivacidad();
});

document.addEventListener("DOMContentLoaded", function () {
  // Detectamos si el dispositivo está en modo responsive
  const isResponsive = window.matchMedia("(max-width: 768px)").matches;

  // Si el dispositivo está en modo responsive, ocultamos el footer al cargar la página
  if (isResponsive) {
    document.querySelector("#footer").style.display = "none";
  }

  window.addEventListener("scroll", function () {
    let scrollPosition = window.scrollY;
    let windowHeight = window.innerHeight;
    let documentHeight = document.body.offsetHeight;
    let triggerPoint = documentHeight - windowHeight - 10;

    // Mostramos el footer cuando se alcanza el punto de activación
    if (scrollPosition > triggerPoint) {
      document.querySelector("#footer").style.display = "block";
    } else {
      // Ocultamos el footer si no se ha alcanzado el punto de activación
      if (isResponsive) {
        document.querySelector("#footer").style.display = "none";
      }
    }
  });
});




function validarNombre() {
  let nombreInput = document.getElementById("nombre");
  let nombreValue = nombreInput.value.trim().toUpperCase(); // Convertir a mayúsculas
  let regexNombreTitular = /^[A-Z]+(?:\s[A-Z]+)*$/; // Expresión regular para aceptar solo mayúsculas y un espacio entre palabras

  // Verificar si el campo tiene algún valor
  if (nombreValue === "") {
      alert("Ingrese su nombre completo");
      return false;
  }

  // Eliminar espacios innecesarios entre palabras
  nombreValue = nombreValue.replace(/\s+/g, ' ');

  // Verificar si hay al menos dos palabras
  let palabras = nombreValue.split(' ');
  if (palabras.length < 2) {
      alert("Ingrese correctamente el nombre");
      nombreInput.value = "";
      return false;
  }

  // Realizar la validación solo si hay datos
  if (!regexNombreTitular.test(nombreValue)) {
      alert("Ingrese un nombre válido");
      nombreInput.value = "";
      return false;
  }

  // Actualizar el valor del campo con el nombre convertido a mayúsculas y sin espacios innecesarios
  nombreInput.value = nombreValue;

  return true;
}





function validarTarjeta() {
  let tarjetaInput = document.getElementById("tarjeta");

  // Verificar si el campo tiene algún valor
  if (tarjetaInput.value.trim() !== "") {
    // Elimina caracteres no numéricos y espacios
    tarjetaInput.value = tarjetaInput.value.replace(/[^0-9]/g, '');

    if (tarjetaInput.value.length !== 16) {
      alert("Coloque los 16 dígitos de la tarjeta");
      tarjetaInput.value = "";
      return false;
    } else {
      // Inserta un espacio cada cuatro dígitos
      tarjetaInput.value = tarjetaInput.value.match(/.{1,4}/g).join(' ');
    }
  }

  return true;
}

function validarFecha() {
  let fechaInput = document.getElementById("fecha");
  let fecha = fechaInput.value.trim().replace(/\s/g, ''); // Eliminar espacios y trim

  // Verificar si el campo tiene algún valor
  if (fecha !== "") {
    // Modificar la expresión regular para permitir la barra diagonal "/"
    if (!/^[0-9]{2}\/[0-9]{2}$/.test(fecha)) {
      alert("Coloque correctamente la fecha de vencimiento (MM/AA)");
      fechaInput.value = "";
      return false;
    } else {
      let mes = parseInt(fecha.slice(0, 2), 10);
      let anio = parseInt(fecha.slice(3), 10);

      if (
        isNaN(mes) || mes < 1 || mes > 12 ||
        isNaN(anio) || anio < 24 || anio > 30
      ) {
        alert("Coloque correctamente la fecha de vencimiento (MM/AA)");
        fechaInput.value = "";
        return false;
      } else {
        // No es necesario modificar la fecha en este caso
      }
    }
  }

  return true;
}


function validarCVV() {
  let cvvInput = document.getElementById("cvv");

  // Verificar si el campo tiene algún valor
  if (cvvInput.value.trim() !== "") {
    // Verificar si hay caracteres no numéricos
    if (/[^0-9]/.test(cvvInput.value)) {
      alert("Coloque correctamente el código de seguridad (solo se permiten números)");
      cvvInput.value = "";
      return false;
    }

    // Remover caracteres no numéricos
    cvvInput.value = cvvInput.value.replace(/[^0-9]/g, '');

    // Verificar si la longitud es diferente de 3
    if (cvvInput.value.length !== 3) {
      alert("Coloque correctamente el código de seguridad (deben ser 3 dígitos)");
      cvvInput.value = "";
      return false;
    }
  }

  return true;
}


function validarDomicilio() {
  // Obtener el valor del campo de domicilio
  let domicilioInput = document.getElementById("domicilio");
  let domicilioValue = domicilioInput.value.trim(); // Eliminar espacios innecesarios

  // Verificar si el campo está vacío
  if (domicilioValue === "") {
      // No hacer nada si el campo está vacío
      return true;
  }

  // Reemplazar espacios adicionales entre palabras y números con un solo espacio
  domicilioValue = domicilioValue.replace(/\s+/g, ' ');

  // Validar el formato del domicilio permitiendo hasta cinco palabras antes de los números,
  // coma (",") y un espacio después de la coma
  const formatoDomicilio = /^(\b[A-Za-z]+\b\s){1,5}\d+,\s*[A-Za-z\s]+$/;

  if (!formatoDomicilio.test(domicilioValue)) {
      // Mostrar alerta si el formato no es válido
      alert('El formato del domicilio no es válido. Ejemplo válido: "Nombre de calle" "123" "," "Localidad".');
      domicilioInput.value = "";
      // Puedes agregar más acciones aquí según tus necesidades
      return false;
  }

  // Actualizar el valor del campo con el domicilio sin espacios innecesarios
  domicilioInput.value = domicilioValue;

  return true;
}




function validarTelefono() {
  let telefonoInput = document.getElementById("telefono");
  let telefonoValue = telefonoInput.value.trim();

  // Verificar si el campo de teléfono no está vacío
  if (telefonoValue !== "") {
    // Verificar si la longitud del número de teléfono es 10 y los primeros dos números son "11"
    if (telefonoValue.length === 10 && telefonoValue.startsWith("11")) {
      // El número de teléfono es válido
    } else {
      alert("Coloque correctamente su número de teléfono");
      telefonoInput.value = "";
      return false;
    }
  }

  return true;
}

function validarEmail() {
  let emailInput = document.getElementById("email");

  // Verificar si se ingresó algún dato
  if (emailInput.value.trim() !== "") {
    let emailRegex = /^[^\s@]+@(gmail\.com|hotmail\.com|outlook\.com)$/;

    // Verificar si el correo cumple con el formato y el dominio
    if (!emailRegex.test(emailInput.value)) {
      alert("Ingrese un correo electrónico válido por favor");
      emailInput.value = "";
      return false;
    }
  }

  return true;
}


// Función para validar el formulario y redireccionar si es válido
function validarYRedireccionar() {
  if (validarFormulario()) {
    redireccionarAFinalizada();
  }
}

// Función para validar el formulario
function validarFormulario() {
  // Obtener los valores de los campos del formulario
  const nombreValue = document.getElementById("nombre").value.trim();
  const tarjetaValue = document.getElementById("tarjeta").value.trim();
  const fechaValue = document.getElementById("fecha").value.trim();
  const cvvValue = document.getElementById("cvv").value.trim();
  const domicilioValue = document.getElementById("domicilio").value.trim();
  const telefonoValue = document.getElementById("telefono").value.trim();
  const emailValue = document.getElementById("email").value.trim();

  // Verificar si algún campo está vacío
  if (nombreValue === "" || tarjetaValue === "" || fechaValue === "" || cvvValue === "" || domicilioValue === "" || telefonoValue === "" || emailValue === "") {
    alert('Por favor, complete todos los campos del formulario.');
    return false;
  }

  // Llamas a las funciones de validación individual
  let nombreValido = validarNombre();
  let tarjetaValida = validarTarjeta();
  let fechaValida = validarFecha();
  let cvvValido = validarCVV();
  let domicilioValido = validarDomicilio();
  let telefonoValido = validarTelefono();
  let emailValido = validarEmail();
  let metodoEnvioSeleccionado = false; // Variable para verificar si se ha seleccionado un método de envío

  // Verificar si todos los campos del formulario están completos y son válidos
  if (!nombreValido || !tarjetaValida || !fechaValida || !cvvValido || !domicilioValido || !telefonoValido || !emailValido) {
    return false;
  }

  // Verificar si se ha seleccionado una opción de envío
  if (radioEnvioDomicilio.checked || radioPuntoEntrega.checked) {
    metodoEnvioSeleccionado = true;
  }

  // Si no se ha seleccionado un método de envío, mostrar una alerta
  if (!metodoEnvioSeleccionado) {
    alert('Seleccione un método de envío.');
    return false;
  }

  // Si el formulario está completo y se ha seleccionado un método de envío, mostrar la alerta de compra finalizada
  alert('Compra finalizada. Le llegará por correo los detalles de la compra');
  document.getElementById('botonPagar').style.display = 'none'; // Oculta el botón de pago
  document.getElementById('tuFormularioId').submit(); // Envía el formulario
  return true;
}

// Función para redireccionar a la página finalizada
function redireccionarAFinalizada() {
  // Redirigir a la página finalizada.html
  window.location.href = "https://grafica-rima.github.io/FinalizarCompra/Pagfin/finalizada.html";
}

// Las funciones de validación individuales y otros códigos relacionados deben ir aquí



document.addEventListener('DOMContentLoaded', function() {
  // Recuperar los detalles de la compra del almacenamiento local
  const carritoGuardado = localStorage.getItem('carrito');
  if (carritoGuardado) {
      const carrito = JSON.parse(carritoGuardado);

      // Mostrar los detalles de la compra en la página
      mostrarDetallesCompra(carrito);
  }
});

function mostrarDetallesCompra(carrito) {
  const detallesCompraElemento = document.getElementById('detallesCompra');

  const tabla = document.createElement('table');
  tabla.innerHTML = `
      <tr>
          <th>Producto</th>
          <th>Precio</th>
          <th>Cantidad</th>
          <th>Total</th>
      </tr>
  `;

  let totalCompra = 0;

  carrito.forEach(item => {
      const fila = document.createElement('tr');
      fila.innerHTML = `
          <td>${item.nombre}</td>
          <td>${item.precio}</td>
          <td>${item.cantidad}</td>
          <td>${(parseFloat(item.precio) * item.cantidad).toFixed(2)}</td>
      `;
      tabla.appendChild(fila);

      totalCompra += parseFloat(item.precio) * item.cantidad;
  });

  const filaTotal = document.createElement('tr');
  filaTotal.innerHTML = `
      <td colspan="3"><strong>Total:</strong></td>
      <td><strong>${totalCompra.toFixed(2)}</strong></td>
  `;
  tabla.appendChild(filaTotal);

  detallesCompraElemento.appendChild(tabla);
}
