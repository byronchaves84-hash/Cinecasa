/*
===========================================================
 CINEMAX — CATÁLOGO CENTRAL + RENDERIZADO
===========================================================

 Funciones:

 - Catálogo central
 - Películas
 - Series
 - Terror
 - Hero dinámico
 - 5 películas del día
 - Contenido aleatorio
 - Búsqueda global
 - Conexión con tarjetas existentes
 - Renderizado automático de series
 - Renderizado automático de terror
 - Renderizado automático de películas
 - Favoritos
 - Recomendaciones
 - Páginas individuales

===========================================================
*/

(function () {

    "use strict";


    /*
    ========================================================
    CATÁLOGO CINEMAX
    ========================================================
    */

    const CINEMAX_CATALOG = {


        /*
        ====================================================
        PELÍCULAS
        ====================================================
        */

        "deadpool-wolverine": {

            id: "deadpool-wolverine",

            title: "Deadpool & Wolverine",

            type: "pelicula",

            year: "2024",

            genres: [
                "Acción",
                "Comedia"
            ],

            image:
                "https://image.tmdb.org/t/p/w500/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg",

            url: "",

            description:
                "Deadpool se une a Wolverine en una aventura llena de acción, humor y caos.",

            featured: true

        },


        "spiderman": {

            id: "spiderman",

            title: "Spider-Man",

            type: "pelicula",

            year: "2021",

            genres: [
                "Acción",
                "Aventura"
            ],

            image:
                "https://image.tmdb.org/t/p/w500/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",

            url: "",

            description:
                "Una nueva aventura del héroe arácnido.",

            featured: true

        },


        "oppenheimer": {

            id: "oppenheimer",

            title: "Oppenheimer",

            type: "pelicula",

            year: "2023",

            genres: [
                "Drama",
                "Historia"
            ],

            image:
                "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",

            url: "",

            description:
                "La historia del científico que estuvo detrás del desarrollo de la bomba atómica.",

            featured: true

        },


        "the-batman": {

            id: "the-batman",

            title: "The Batman",

            type: "pelicula",

            year: "2022",

            genres: [
                "Acción",
                "Crimen"
            ],

            image:
                "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg",

            url: "",

            description:
                "Batman se enfrenta a una serie de crímenes que revelan una oscura conspiración en Gotham.",

            featured: true

        },


        "avengers": {

            id: "avengers",

            title: "Avengers",

            type: "pelicula",

            year: "2012",

            genres: [
                "Acción",
                "Fantasía"
            ],

            image:
                "https://image.tmdb.org/t/p/w500/4ssDuvEDkSArWEdyBl2X5EHvYKU.jpg",

            url: "",

            description:
                "Los héroes más poderosos de la Tierra deben unirse para defender el planeta.",

            featured: true

        },


        "interstellar": {

            id: "interstellar",

            title: "Interstellar",

            type: "pelicula",

            year: "2014",

            genres: [
                "Ciencia ficción",
                "Drama"
            ],

            image:
                "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",

            url: "",

            description:
                "Una misión más allá de los límites del espacio en busca de un nuevo hogar para la humanidad.",

            featured: true

        },


        /*
        ====================================================
        SERIES
        ====================================================
        */

        "serie-1": {

            id: "serie-1",

            title: "Serie 1",

            type: "serie",

            year: "",

            genres: [
                "Serie"
            ],

            image:
                "../Cinema-main/images/serie1.jpg",

            url:
                "../Cinema-main/Serie1/index.html",

            description:
                "Descubre la historia de Serie 1.",

            featured: false

        },


        "serie-2": {

            id: "serie-2",

            title: "Serie 2",

            type: "serie",

            year: "",

            genres: [
                "Serie"
            ],

            image:
                "../Cinema-main/images/serie2.jpg",

            url:
                "../Cinema-main/Serie2/index.html",

            description:
                "Descubre la historia de Serie 2.",

            featured: false

        },


        "serie-3": {

            id: "serie-3",

            title: "Serie 3",

            type: "serie",

            year: "",

            genres: [
                "Serie"
            ],

            image:
                "../Cinema-main/images/serie3.jpg",

            url:
                "../Cinema-main/Serie3/index.html",

            description:
                "Descubre la historia de Serie 3.",

            featured: false

        },


        "serie-4": {

            id: "serie-4",

            title: "Serie 4",

            type: "serie",

            year: "",

            genres: [
                "Serie"
            ],

            image:
                "../Cinema-main/images/serie4.jpg",

            url:
                "../Cinema-main/Serie 4/index.html",

            description:
                "Descubre la historia de Serie 4.",

            featured: false

        },


        "serie-5": {

            id: "serie-5",

            title: "Serie 5",

            type: "serie",

            year: "",

            genres: [
                "Serie"
            ],

            image:
                "../Cinema-main/images/serie5.jpg",

            url:
                "../Cinema-main/Serie /index.html",

            description:
                "Descubre la historia de Serie 5.",

            featured: false

        },


        "serie-6": {

            id: "serie-6",

            title: "Serie 6",

            type: "serie",

            year: "",

            genres: [
                "Serie"
            ],

            image:
                "../Cinema-main/images/serie6.jpg",

            url:
                "../Cinema-main/Serie 6/index.html",

            description:
                "Descubre la historia de Serie 6.",

            featured: false

        },


        "serie-7": {

            id: "serie-7",

            title: "Serie 7",

            type: "serie",

            year: "",

            genres: [
                "Serie"
            ],

            image:
                "../Cinema-main/images/serie7.jpg",

            url:
                "../Cinema-main/Serie7/index.html",

            description:
                "Descubre la historia de Serie 7.",

            featured: false

        },


        "serie-8": {

            id: "serie-8",

            title: "Serie 8",

            type: "serie",

            year: "",

            genres: [
                "Serie"
            ],

            image:
                "../Cinema-main/images/serie8.jpg",

            url:
                "../Cinema-main/Serie8/index.html",

            description:
                "Descubre la historia de Serie 8.",

            featured: false

        },


        "serie-9": {

            id: "serie-9",

            title: "Serie 9",

            type: "serie",

            year: "",

            genres: [
                "Serie"
            ],

            image:
                "../Cinema-main/images/serie9.jpg",

            url:
                "../Cinema-main/serie9/index.html",

            description:
                "Descubre la historia de Serie 9.",

            featured: false

        },


        /*
        ====================================================
        TERROR
        ====================================================
        */

        "terror-1": {

            id: "terror-1",

            title: "Terror 1",

            type: "terror",

            year: "",

            genres: [
                "Terror"
            ],

            image:
                "../Cinema-main/images/terror1.jpg",

            url:
                "../Cinema-main/terror1/enlace1.html",

            description:
                "Una historia para quienes se atreven a mirar.",

            featured: false

        },


        "terror-2": {

            id: "terror-2",

            title: "Terror 2",

            type: "terror",

            year: "",

            genres: [
                "Terror"
            ],

            image:
                "../Cinema-main/images/terror2.jpg",

            url:
                "../Cinema-main/terror2/enlace1.html",

            description:
                "Una nueva historia de terror.",

            featured: false

        },


        "terror-3": {

            id: "terror-3",

            title: "Terror 3",

            type: "terror",

            year: "",

            genres: [
                "Terror"
            ],

            image:
                "../Cinema-main/images/terror3.jpg",

            url:
                "../Cinema-main/terror3/enlace1.html",

            description:
                "Una historia de terror para quienes se atreven a mirar.",

            featured: false

        },


        "terror-4": {

            id: "terror-4",

            title: "Terror 4",

            type: "terror",

            year: "",

            genres: [
                "Terror"
            ],

            image:
                "../Cinema-main/images/terror6.jpg",

            url:
                "../Cinema-main/terror4/enlace1.html",

            description:
                "Una nueva pesadilla comienza.",

            featured: false

        },


        "terror-5": {

            id: "terror-5",

            title: "Terror 5",

            type: "terror",

            year: "",

            genres: [
                "Terror"
            ],

            image:
                "../Cinema-main/images/terror7.jpg",

            url:
                "../Cinema-main/terror5/enlace1.html",

            description:
                "Una historia oscura que pondrá a prueba tu valor.",

            featured: false

        },


        "terror-6": {

            id: "terror-6",

            title: "Terror 6",

            type: "terror",

            year: "",

            genres: [
                "Terror"
            ],

            image:
                "../Cinema-main/images/terror8.jpg",

            url:
                "../Cinema-main/terror6/enlace1.html",

            description:
                "El miedo vuelve a comenzar.",

            featured: false

        },


        "terror-7": {

            id: "terror-7",

            title: "Terror 7",

            type: "terror",

            year: "",

            genres: [
                "Terror"
            ],

            image:
                "../Cinema-main/images/terror9.jpg",

            url:
                "../Cinema-main/terror7/enlace1.html",

            description:
                "No todo lo que ves debería estar ahí.",

            featured: false

        },


        "terror-8": {

            id: "terror-8",

            title: "Terror 8",

            type: "terror",

            year: "",

            genres: [
                "Terror"
            ],

            image:
                "../Cinema-main/images/terror10.jpg",

            url:
                "../Cinema-main/terror8/enlace1.html",

            description:
                "Una nueva pesadilla espera en la oscuridad.",

            featured: false

        },


        "terror-9": {

            id: "terror-9",

            title: "Terror 9",

            type: "terror",

            year: "",

            genres: [
                "Terror"
            ],

            image:
                "../Cinema-main/images/terror11.jpg",

            url:
                "../Cinema-main/terror9/enlace1.html",

            description:
                "El terror nunca termina.",

            featured: false

        }

    };


    /*
    ========================================================
    ALIAS GLOBAL
    ========================================================
    */

    window.CINEMAX_CATALOG =
        CINEMAX_CATALOG;


    /*
    ========================================================
    API CINEMAX
    ========================================================
    */

    window.CinemaX = {

        catalog: CINEMAX_CATALOG,


        /*
        ====================================================
        OBTENER UNO
        ====================================================
        */

        get: function (id) {

            if (!id) {
                return null;
            }

            return (
                CINEMAX_CATALOG[
                    String(id)
                ] || null
            );

        },


        /*
        ====================================================
        OBTENER TODO
        ====================================================
        */

        getAll: function () {

            return Object.values(
                CINEMAX_CATALOG
            );

        },


        /*
        ====================================================
        PELÍCULAS
        ====================================================
        */

        getMovies: function () {

            return Object.values(
                CINEMAX_CATALOG
            ).filter(
                item =>
                    item.type === "pelicula"
            );

        },


        /*
        ====================================================
        SERIES
        ====================================================
        */

        getSeries: function () {

            return Object.values(
                CINEMAX_CATALOG
            ).filter(
                item =>
                    item.type === "serie"
            );

        },


        /*
        ====================================================
        TERROR
        ====================================================
        */

        getHorror: function () {

            return Object.values(
                CINEMAX_CATALOG
            ).filter(
                item =>
                    item.type === "terror"
            );

        },


        /*
        ====================================================
        DESTACADAS
        ====================================================
        */

        getFeatured: function () {

            return Object.values(
                CINEMAX_CATALOG
            ).filter(
                item =>
                    item.featured === true
            );

        },


        /*
        ====================================================
        BÚSQUEDA GLOBAL
        ====================================================
        */

        search: function (query) {

            const clean =
                String(query || "")
                    .toLowerCase()
                    .normalize("NFD")
                    .replace(
                        /[\u0300-\u036f]/g,
                        ""
                    )
                    .trim();


            if (!clean) {
                return [];
            }


            return Object.values(
                CINEMAX_CATALOG
            ).filter(item => {

                const searchable = [

                    item.title,

                    item.type,

                    item.year,

                    item.description,

                    ...(item.genres || [])

                ]
                    .join(" ")
                    .toLowerCase()
                    .normalize("NFD")
                    .replace(
                        /[\u0300-\u036f]/g,
                        ""
                    );


                return searchable.includes(
                    clean
                );

            });

        },


        /*
        ====================================================
        5 PELÍCULAS DEL DÍA
        ====================================================
        */

        getDailyMovies: function () {

            const movies =
                this.getMovies();


            if (movies.length <= 5) {
                return [...movies];
            }


            const now =
                new Date();


            const dateKey =
                now.getFullYear() +
                "-" +
                String(
                    now.getMonth() + 1
                ).padStart(2, "0") +
                "-" +
                String(
                    now.getDate()
                ).padStart(2, "0");


            const storageKey =
                "cinemax_daily_movies";


            let saved = null;


            try {

                saved =
                    JSON.parse(
                        localStorage.getItem(
                            storageKey
                        )
                    );

            } catch (error) {

                saved = null;

            }


            if (

                saved &&

                saved.date === dateKey &&

                Array.isArray(
                    saved.ids
                )

            ) {

                const dailyMovies =
                    saved.ids
                        .map(
                            id =>
                                this.get(id)
                        )
                        .filter(
                            Boolean
                        );


                if (
                    dailyMovies.length === 5
                ) {

                    return dailyMovies;

                }

            }


            const shuffled =
                [...movies];


            for (
                let i =
                    shuffled.length - 1;

                i > 0;

                i--
            ) {

                const j =
                    Math.floor(
                        Math.random() *
                        (i + 1)
                    );


                [
                    shuffled[i],
                    shuffled[j]
                ] = [
                    shuffled[j],
                    shuffled[i]
                ];

            }


            const selected =
                shuffled.slice(
                    0,
                    5
                );


            try {

                localStorage.setItem(

                    storageKey,

                    JSON.stringify({

                        date:
                            dateKey,

                        ids:
                            selected.map(
                                movie =>
                                    movie.id
                            )

                    })

                );

            } catch (error) {

                console.warn(
                    "CinemaX: no se pudo guardar las películas del día.",
                    error
                );

            }


            return selected;

        },


        /*
        ====================================================
        PELÍCULA ALEATORIA
        ====================================================
        */

        getRandomMovie: function () {

            const movies =
                this.getMovies();


            if (!movies.length) {
                return null;
            }


            return movies[
                Math.floor(
                    Math.random() *
                    movies.length
                )
            ];

        },


        /*
        ====================================================
        CONTENIDO ALEATORIO
        ====================================================
        */

        getRandom: function () {

            const all =
                this.getAll();


            if (!all.length) {
                return null;
            }


            return all[
                Math.floor(
                    Math.random() *
                    all.length
                )
            ];

        }

    };


    /*
    ========================================================
    CREAR TARJETA
    ========================================================
    */

    function createMovieCard(item) {

        const card =
            document.createElement(
                "article"
            );


        card.className =
            "movie-card";


        card.dataset.id =
            item.id;


        card.dataset.cinemaxId =
            item.id;


        card.dataset.type =
            item.type;


        if (item.year) {

            card.dataset.year =
                item.year;

        }


        if (item.genres?.length) {

            card.dataset.genre =
                item.genres.join(
                    ", "
                );

        }


        if (item.url) {

            card.dataset.url =
                item.url;

        }


        /*
        ----------------------------------------------------
        TARJETA
        ----------------------------------------------------
        */

        card.innerHTML = `

            <div class="movie-poster">

                <img
                    src="${item.image}"
                    alt="${item.title}"
                    loading="lazy"
                >

            </div>

            <div class="movie-info">

                <h3>
                    ${item.title}
                </h3>

                ${
                    item.year
                        ? `<span>${item.year}</span>`
                        : ""
                }

            </div>

        `;


        /*
        ----------------------------------------------------
        CLICK
        ----------------------------------------------------
        */

        card.addEventListener(
            "click",
            function () {

                if (
                    item.url &&
                    item.url.trim()
                ) {

                    window.location.href =
                        item.url;

                }

            }
        );


        /*
        ----------------------------------------------------
        ERROR IMAGEN
        ----------------------------------------------------
        */

        const image =
            card.querySelector(
                "img"
            );


        if (image) {

            image.addEventListener(
                "error",
                function () {

                    this.style.display =
                        "none";

                }
            );

        }


        return card;

    }


    /*
    ========================================================
    RENDERIZAR CATÁLOGO
    ========================================================
    */

    function renderCatalogSection(
        container,
        items
    ) {

        if (!container) {
            return;
        }


        container.innerHTML = "";


        items.forEach(
            item => {

                container.appendChild(
                    createMovieCard(item)
                );

            }
        );

    }


    /*
    ========================================================
    BUSCAR CONTENEDORES
    ========================================================
    */

    function findContainer(
        selectors
    ) {

        for (
            const selector of selectors
        ) {

            const element =
                document.querySelector(
                    selector
                );


            if (element) {
                return element;
            }

        }


        return null;

    }


    /*
    ========================================================
    RENDERIZAR SERIES
    ========================================================
    */

    function renderSeries() {

        const container =
            findContainer([

                "#seriesCatalog",

                "#series-container",

                "#seriesGrid",

                ".series-grid",

                ".series-container",

                '[data-catalog="series"]'

            ]);


        if (!container) {

            console.warn(
                "CinemaX: no se encontró el contenedor de series."
            );

            return;

        }


        renderCatalogSection(

            container,

            CinemaX.getSeries()

        );

    }


    /*
    ========================================================
    RENDERIZAR TERROR
    ========================================================
    */

    function renderHorror() {

        const container =
            findContainer([

                "#horrorCatalog",

                "#terrorCatalog",

                "#terror-container",

                "#terrorGrid",

                ".terror-grid",

                ".terror-container",

                '[data-catalog="terror"]'

            ]);


        if (!container) {
            return;
        }


        renderCatalogSection(

            container,

            CinemaX.getHorror()

        );

    }


    /*
    ========================================================
    RENDERIZAR PELÍCULAS
    ========================================================
    */

    function renderMovies() {

        const container =
            findContainer([

                "#moviesCatalog",

                "#movieCatalog",

                "#movies-container",

                "#moviesGrid",

                ".movies-grid",

                ".movies-container",

                '[data-catalog="movies"]'

            ]);


        if (!container) {
            return;
        }


        renderCatalogSection(

            container,

            CinemaX.getMovies()

        );

    }


    /*
    ========================================================
    RENDERIZAR 5 PELÍCULAS DEL DÍA
    ========================================================
    */

    function renderDailyMovies() {

        const container =
            findContainer([

                "#dailyMovies",

                "#dailyMoviesCatalog",

                "#daily-movies",

                "#todayMovies",

                '[data-catalog="daily"]'

            ]);


        if (!container) {
            return;
        }


        renderCatalogSection(

            container,

            CinemaX.getDailyMovies()

        );

    }


    /*
    ========================================================
    CONECTAR TARJETAS EXISTENTES
    ========================================================
    */

    function connectCards() {

        document
            .querySelectorAll(
                ".movie-card"
            )
            .forEach(card => {


                const existingId =
                    card.dataset.id;


                if (!existingId) {
                    return;
                }


                const item =
                    CINEMAX_CATALOG[
                        existingId
                    ];


                if (!item) {
                    return;
                }


                card.dataset.cinemaxId =
                    item.id;


                if (

                    item.year &&

                    !card.dataset.year

                ) {

                    card.dataset.year =
                        item.year;

                }


                if (

                    item.genres &&

                    item.genres.length &&

                    !card.dataset.genre

                ) {

                    card.dataset.genre =
                        item.genres.join(
                            ", "
                        );

                }


                if (

                    item.type &&

                    !card.dataset.type

                ) {

                    card.dataset.type =
                        item.type;

                }


                if (

                    !card.dataset.url &&

                    item.url

                ) {

                    card.dataset.url =
                        item.url;

                }


                const image =
                    card.querySelector(
                        ".movie-poster img"
                    );


                if (

                    image &&

                    !image.getAttribute(
                        "src"
                    ) &&

                    item.image

                ) {

                    image.src =
                        item.image;

                }

            });

    }


    /*
    ========================================================
    CREAR SECCIONES AUTOMÁTICAS
    ========================================================
    */

    function createAutomaticSections() {

        const main =
            document.querySelector(
                "main"
            );


        if (!main) {
            return;
        }


        /*
        ----------------------------------------------------
        SERIES
        ----------------------------------------------------
        */

        let seriesContainer =
            document.getElementById(
                "seriesCatalog"
            );


        if (!seriesContainer) {

            const section =
                document.createElement(
                    "section"
                );


            section.className =
                "catalog-section cinemax-auto-section";


            section.innerHTML = `

                <div class="section-header">

                    <h2>Series</h2>

                </div>

                <div
                    class="movie-grid"
                    id="seriesCatalog"
                ></div>

            `;


            main.appendChild(
                section
            );


            seriesContainer =
                section.querySelector(
                    "#seriesCatalog"
                );

        }


        /*
        ----------------------------------------------------
        TERROR
        ----------------------------------------------------
        */

        let horrorContainer =
            document.getElementById(
                "terrorCatalog"
            );


        if (!horrorContainer) {

            const section =
                document.createElement(
                    "section"
                );


            section.className =
                "catalog-section cinemax-auto-section";


            section.innerHTML = `

                <div class="section-header">

                    <h2>Terror</h2>

                </div>

                <div
                    class="movie-grid"
                    id="terrorCatalog"
                ></div>

            `;


            main.appendChild(
                section
            );


            horrorContainer =
                section.querySelector(
                    "#terrorCatalog"
                );

        }

    }


    /*
    ========================================================
    FAVORITOS
    ========================================================
    */

    const Favorites = {

        key:
            "cinemax_favorites",


        get: function () {

            try {

                return JSON.parse(
                    localStorage.getItem(
                        this.key
                    )
                ) || [];

            } catch {

                return [];

            }

        },


        has: function (id) {

            return this
                .get()
                .includes(id);

        },


        add: function (id) {

            const favorites =
                this.get();


            if (
                !favorites.includes(id)
            ) {

                favorites.push(id);

            }


            localStorage.setItem(

                this.key,

                JSON.stringify(
                    favorites
                )

            );

        },


        remove: function (id) {

            const favorites =
                this
                    .get()
                    .filter(
                        favorite =>
                            favorite !== id
                    );


            localStorage.setItem(

                this.key,

                JSON.stringify(
                    favorites
                )

            );

        },


        toggle: function (id) {

            if (
                this.has(id)
            ) {

                this.remove(id);

                return false;

            }


            this.add(id);

            return true;

        }

    };


    /*
    ========================================================
    EXPONER FAVORITOS
    ========================================================
    */

    window.CinemaXFavorites =
        Favorites;


    /*
    ========================================================
    ABRIR CONTENIDO
    ========================================================
    */

    window.CinemaXOpen =
        function (id) {

            const item =
                CinemaX.get(id);


            if (!item) {
                return;
            }


            if (
                item.url &&
                item.url.trim()
            ) {

                window.location.href =
                    item.url;

            }

        };


    /*
    ========================================================
    INICIALIZACIÓN
    ========================================================
    */

    function initializeCinemaX() {

        /*
        ----------------------------------------------------
        PRIMERO CONECTAMOS LAS TARJETAS
        EXISTENTES
        ----------------------------------------------------
        */

        connectCards();


        /*
        ----------------------------------------------------
        CREAMOS LAS SECCIONES SI NO EXISTEN
        ----------------------------------------------------
        */

        createAutomaticSections();


        /*
        ----------------------------------------------------
        RENDERIZAMOS SERIES
        ----------------------------------------------------
        */

        renderSeries();


        /*
        ----------------------------------------------------
        RENDERIZAMOS TERROR
        ----------------------------------------------------
        */

        renderHorror();


        /*
        ----------------------------------------------------
        PELÍCULAS
        ----------------------------------------------------

        Solo se renderizan automáticamente si
        existe un contenedor específico.

        Así no reemplazamos tu catálogo actual.

        ----------------------------------------------------
        */

        renderMovies();


        /*
        ----------------------------------------------------
        5 PELÍCULAS DEL DÍA
        ----------------------------------------------------
        */

        renderDailyMovies();


        /*
        ----------------------------------------------------
        EVENTO GLOBAL
        ----------------------------------------------------
        */

        document.dispatchEvent(

            new CustomEvent(
                "cinemax:ready",
                {
                    detail: {
                        catalog:
                            CINEMAX_CATALOG
                    }
                }
            )

        );


        console.log(
            "🎬 CinemaX catálogo cargado:",
            CinemaX.getAll().length,
            "contenidos."
        );


        console.log(
            "📺 Series:",
            CinemaX.getSeries().length
        );


        console.log(
            "👻 Terror:",
            CinemaX.getHorror().length
        );


        console.log(
            "🎬 Películas:",
            CinemaX.getMovies().length
        );

    }


    /*
    ========================================================
    DOM READY
    ========================================================
    */

    if (

        document.readyState ===
        "loading"

    ) {

        document.addEventListener(

            "DOMContentLoaded",

            initializeCinemaX

        );

    } else {

        initializeCinemaX();

    }


})();