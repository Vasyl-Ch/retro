/** @type {import('tailwindcss').Config} */
// import themer from "@tailus/themer"; // if i delete this i got an error
const defaultTheme = require("tailwindcss/defaultTheme");

module.exports = {
    content: [
        "./*.html",
        "./*.js",
        "./src/**/*.html",
        "./src/**/*.js",
        "../distributor/templates/**/*.html",
        "../distributor/apps/**/templates/**/*.html",
        "/app/templates/**/*.html",
        "/app/apps/**/templates/**/*.html",
    ],
    darkMode: "media",
    safelist: ["isToggled"],
    theme: {
        fontFamily: {
            sans: ['Geist', 'Inter', ...defaultTheme.fontFamily.sans],
            mono : ['GeistMono', 'fira-code', ...defaultTheme.fontFamily.mono],
        },
        extend: {
            colors: ({ colors }) => ({
                primary: {
                    50:  'rgb(var(--primary-50) / <alpha-value>)',
                    100: 'rgb(var(--primary-100) / <alpha-value>)',
                    200: 'rgb(var(--primary-200) / <alpha-value>)',
                    300: 'rgb(var(--primary-300) / <alpha-value>)',
                    400: 'rgb(var(--primary-400) / <alpha-value>)',
                    500: 'rgb(var(--primary-500) / <alpha-value>)',
                    600: 'rgb(var(--primary-600) / <alpha-value>)',
                    700: 'rgb(var(--primary-700) / <alpha-value>)',
                    800: 'rgb(var(--primary-800) / <alpha-value>)',
                    900: 'rgb(var(--primary-900) / <alpha-value>)',
                    950: 'rgb(var(--primary-950) / <alpha-value>)',
                    DEFAULT: 'rgb(var(--primary-600) / <alpha-value>)',
                },
                danger : colors.rose,
                warning : colors.yellow,
                success : colors.lime,
                info : colors.blue,
                gray : colors.zinc,
            }),
        }
        
    },
    plugins: [],
};
