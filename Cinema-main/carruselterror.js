```javascript
// =========================================================
// CINEMAX — CARRUSELES PC + MÓVIL TÁCTIL
// =========================================================


// =========================================================
// CARRUSEL DE SERIES
// =========================================================

const seriesCarousel =
    document.getElementById("seriesCarousel");

const seriesTrack =
    seriesCarousel
        ? seriesCarousel.querySelector(".carousel-track")
        : null;

const seriesCards =
    seriesTrack
        ? seriesTrack.querySelectorAll(".series-card")
        : [];

let seriesPosition = 0;


// =========================================================
// MOVER SERIES EN PC
// =========================================================

function moveSeries(direction) {

    // En móvil las flechas no hacen nada.
    // El usuario desliza directamente.
    if (window.innerWidth <= 600) {
        return;
    }

    if (!seriesTrack || !seriesCards.length) {
        return;
    }

    const gap = 18;

    const cardWidth =
        seriesCards[0].offsetWidth + gap;

    const visibleCards =
        Math.floor(
            seriesCarousel.offsetWidth / cardWidth
        );

    const maxPosition =
        Math.max(
            0,
            seriesCards.length - visibleCards
        );

    seriesPosition += direction;


    // No permitir pasar del principio
    if (seriesPosition < 0) {
        seriesPosition = 0;
    }


    // No permitir pasar del final
    if (seriesPosition > maxPosition) {
        seriesPosition = maxPosition;
    }


    seriesTrack.style.transform =
        `translateX(-${seriesPosition * cardWidth}px)`;
}


// =========================================================
// TÁCTIL — SERIES
// =========================================================

if (seriesCarousel) {

    let seriesStartX = 0;
    let seriesStartY = 0;


    seriesCarousel.addEventListener(
        "touchstart",
        function (event) {

            seriesStartX =
                event.touches[0].clientX;

            seriesStartY =
                event.touches[0].clientY;

        },
        { passive: true }
    );


    seriesCarousel.addEventListener(
        "touchend",
        function (event) {

            const seriesEndX =
                event.changedTouches[0].clientX;

            const seriesEndY =
                event.changedTouches[0].clientY;


            const differenceX =
                seriesStartX - seriesEndX;

            const differenceY =
                seriesStartY - seriesEndY;


            // Solo detectar deslizamientos horizontales
            if (
                Math.abs(differenceX) >
                Math.abs(differenceY)
            ) {

                // Deslizar hacia la izquierda
                if (differenceX > 50) {

                    seriesCarousel.scrollBy({
                        left: 185,
                        behavior: "smooth"
                    });

                }


                // Deslizar hacia la derecha
                if (differenceX < -50) {

                    seriesCarousel.scrollBy({
                        left: -185,
                        behavior: "smooth"
                    });

                }

            }

        },
        { passive: true }
    );
}


// =========================================================
// CARRUSEL DE TERROR
// =========================================================

const horrorCarousel =
    document.getElementById("horrorCarousel");

const horrorTrack =
    horrorCarousel
        ? horrorCarousel.querySelector(".carousel-track")
        : null;

const horrorCards =
    horrorTrack
        ? horrorTrack.querySelectorAll(".horror-card")
        : [];

let horrorPosition = 0;


// =========================================================
// MOVER TERROR EN PC
// =========================================================

function moveHorror(direction) {

    // En móvil usamos desplazamiento táctil
    if (window.innerWidth <= 600) {
        return;
    }

    if (!horrorTrack || !horrorCards.length) {
        return;
    }

    const gap = 18;

    const cardWidth =
        horrorCards[0].offsetWidth + gap;

    const visibleCards =
        Math.floor(
            horrorCarousel.offsetWidth / cardWidth
        );

    const maxPosition =
        Math.max(
            0,
            horrorCards.length - visibleCards
        );

    horrorPosition += direction;


    // Principio
    if (horrorPosition < 0) {
        horrorPosition = 0;
    }


    // Final
    if (horrorPosition > maxPosition) {
        horrorPosition = maxPosition;
    }


    horrorTrack.style.transform =
        `translateX(-${horrorPosition * cardWidth}px)`;
}


// =========================================================
// TÁCTIL — TERROR
// =========================================================

if (horrorCarousel) {

    let horrorStartX = 0;
    let horrorStartY = 0;


    horrorCarousel.addEventListener(
        "touchstart",
        function (event) {

            horrorStartX =
                event.touches[0].clientX;

            horrorStartY =
                event.touches[0].clientY;

        },
        { passive: true }
    );


    horrorCarousel.addEventListener(
        "touchend",
        function (event) {

            const horrorEndX =
                event.changedTouches[0].clientX;

            const horrorEndY =
                event.changedTouches[0].clientY;


            const differenceX =
                horrorStartX - horrorEndX;

            const differenceY =
                horrorStartY - horrorEndY;


            // Solo movimiento horizontal
            if (
                Math.abs(differenceX) >
                Math.abs(differenceY)
            ) {

                // Deslizar izquierda
                if (differenceX > 50) {

                    horrorCarousel.scrollBy({
                        left: 195,
                        behavior: "smooth"
                    });

                }


                // Deslizar derecha
                if (differenceX < -50) {

                    horrorCarousel.scrollBy({
                        left: -195,
                        behavior: "smooth"
                    });

                }

            }

        },
        { passive: true }
    );
}


// =========================================================
// BOTONES DE SERIES
// =========================================================

const nextSeriesButton =
    document.querySelector(".next-series");

const prevSeriesButton =
    document.querySelector(".prev-series");


if (nextSeriesButton) {

    nextSeriesButton.addEventListener(
        "click",
        function () {
            moveSeries(1);
        }
    );

}


if (prevSeriesButton) {

    prevSeriesButton.addEventListener(
        "click",
        function () {
            moveSeries(-1);
        }
    );

}


// =========================================================
// BOTONES DE TERROR
// =========================================================

const nextHorrorButton =
    document.querySelector(".next-horror");

const prevHorrorButton =
    document.querySelector(".prev-horror");


if (nextHorrorButton) {

    nextHorrorButton.addEventListener(
        "click",
        function () {
            moveHorror(1);
        }
    );

}


if (prevHorrorButton) {

    prevHorrorButton.addEventListener(
        "click",
        function () {
            moveHorror(-1);
        }
    );

}


// =========================================================
// REAJUSTAR AL CAMBIAR TAMAÑO
// =========================================================

window.addEventListener(
    "resize",
    function () {

        seriesPosition = 0;
        horrorPosition = 0;


        if (seriesTrack) {

            seriesTrack.style.transform =
                "translateX(0)";

        }


        if (horrorTrack) {

            horrorTrack.style.transform =
                "translateX(0)";

        }

    }
);
```

