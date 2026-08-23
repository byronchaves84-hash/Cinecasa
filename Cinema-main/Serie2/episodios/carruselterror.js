// Variables para controlar el carrusel de terror
let horrorCurrentIndex = 0;  // Índice de la imagen actual
const horrorImages = document.querySelectorAll('.horror-carousel-images .horror-anime-item');  // Seleccionamos todos los elementos del carrusel de terror
const horrorTotalImages = horrorImages.length;  // Total de elementos en el carrusel de terror

// Ancho de cada item + margen (ancho: 280px, margen: 15px)
const horrorItemWidth = 280 + 15;  // 280px de ancho + 15px de margen

// Función para cambiar la imagen mostrada en el carrusel de terror
function changeHorrorImage() {
    // Calculamos el desplazamiento
    const offset = -horrorCurrentIndex * horrorItemWidth;  // Desplazamos el contenedor de acuerdo al índice y al tamaño total del item
    // Aplicamos el desplazamiento al contenedor de imágenes
    document.querySelector('.horror-carousel-images').style.transform = `translateX(${offset}px)`;
}

// Función para mover al siguiente en el carrusel de terror
function nextHorrorImage() {
    // Incrementamos el índice y lo volvemos a cero si llegamos al final
    horrorCurrentIndex = (horrorCurrentIndex + 1) % horrorTotalImages;
    changeHorrorImage();
}

// Función para mover a la imagen anterior en el carrusel de terror
function prevHorrorImage() {
    // Decrementamos el índice y lo volvemos al final si llegamos al principio
    horrorCurrentIndex = (horrorCurrentIndex - 1 + horrorTotalImages) % horrorTotalImages;
    changeHorrorImage();
}

// Añadir eventos a los botones del carrusel de terror
document.querySelector('.next-horror').addEventListener('click', nextHorrorImage);
document.querySelector('.prev-horror').addEventListener('click', prevHorrorImage);
