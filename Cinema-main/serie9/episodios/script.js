// Selecciona todas las opiniones ocultas y los botones
const episodiosOcultos = document.querySelectorAll('.episodio.oculta');
const botonVerMas = document.getElementById('ver-mas');
const botonVerMenos = document.getElementById('ver-menos');

// Muestra solo 4 episodios por fila
const maxEpisodiosPorFila = 4;
const totalEpisodios = episodiosOcultos.length;
const totalEpisodiosVisibles = document.querySelectorAll('.episodio').length - episodiosOcultos.length;

if (totalEpisodiosVisibles >= maxEpisodiosPorFila) {
    botonVerMas.style.display = 'block'; // Muestra el botón "Ver más"
}

// Evento para el botón "Ver más"
botonVerMas.addEventListener('click', () => {
    // Muestra los episodios ocultos
    episodiosOcultos.forEach(episodio => {
        episodio.style.display = 'block';
    });
    // Oculta el botón "Ver más" y muestra "Ver menos"
    botonVerMas.style.display = 'none';
    botonVerMenos.style.display = 'block';
});

// Evento para el botón "Ver menos"
botonVerMenos.addEventListener('click', () => {
    // Oculta los episodios adicionales
    episodiosOcultos.forEach(episodio => {
        episodio.style.display = 'none';
    });
    // Oculta el botón "Ver menos" y muestra "Ver más"
    botonVerMenos.style.display = 'none';
    botonVerMas.style.display = 'block';
});
