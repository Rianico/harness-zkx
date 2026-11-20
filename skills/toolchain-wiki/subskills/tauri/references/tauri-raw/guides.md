<SYSTEM>Guides: guides, concepts, and tutorials for developing and distributing Tauri applications</SYSTEM>

# What is Tauri?

> Information for getting up and running with Tauri, including prerequisites and installation instructions

Tauri is a framework for building tiny, fast binaries for all major desktop and mobile platforms. Developers can integrate any frontend framework that compiles to HTML, JavaScript, and CSS for building their user experience while leveraging languages such as Rust, Swift, and Kotlin for backend logic when needed. Get started building with [`create-tauri-app`](https://github.com/tauri-apps/create-tauri-app) by using one of the below commands. Be sure to follow the [prerequisites guide](/start/prerequisites/) to install all of the dependencies required by Tauri. For a more detailed walkthrough, see [Create a Project](/start/create-project/#using-create-tauri-app) * Bash 
  ```sh
  sh <(curl https://create.tauri.app/sh)
  ```
 * PowerShell 
  ```sh
  irm https://create.tauri.app/ps | iex
  ```
 * Fish 
  ```sh
  sh (curl -sSL https://create.tauri.app/sh | psub)
  ```
 * npm 
  ```sh
  npm create tauri-app@latest
  ```
 * Yarn 
  ```sh
  yarn create tauri-app
  ```
 * pnpm 
  ```sh
  pnpm create tauri-app
  ```
 * deno 
  ```sh
  deno run -A npm:create-tauri-app
  ```
 * bun 
  ```sh
  bun create tauri-app
  ```
 * Cargo 
  ```sh
  cargo install create-tauri-app --locked
  cargo create-tauri-app
  ```
 After you’ve created your first app, take a look at [Project Structure](/start/project-structure/) to understand what each file does. Or explore the project setups and features from the examples ([tauri](https://github.com/tauri-apps/tauri/tree/dev/examples) | [plugins-workspace](https://github.com/tauri-apps/plugins-workspace/tree/v2/examples/api)) ## Why Tauri? Tauri has 3 main advantages for developers to build upon: * Secure foundation for building apps * Smaller bundle size by using the system’s native webview * Flexibility for developers to use any frontend and bindings for multiple languages Learn more about the Tauri philosophy in the [Tauri 1.0 blog post](/blog/tauri-1-0/). ### Secure Foundation By being built on Rust, Tauri is able to take advantage of the memory safety, thread safety, and type-safety offered by Rust. Apps built on Tauri can automatically get those benefits even without needing to be developed by Rust experts. Tauri also undergoes a security audit for major and minor releases. This not only covers code in the Tauri organization, but also for upstream dependencies that Tauri relies on. Of course this doesn’t mitigate all risks, but it provides a solid foundation for developers to build on top of. Read the [Tauri security policy](https://github.com/tauri-apps/tauri/security/policy) and the [Tauri 2.0 audit report](https://github.com/tauri-apps/tauri/blob/dev/audits/Radically_Open_Security-v2-report.pdf). ### Smaller App Size Tauri apps take advantage of the web view already available on every user’s system. A Tauri app only contains the code and assets specific for that app and doesn’t need to bundle a browser engine with every app. This means that a minimal Tauri app can be less than 600KB in size. Learn more about creating optimized apps in the [App Size concept](/concept/size/). ### Flexible Architecture Since Tauri uses web technologies that means that virtually any frontend framework is compatible with Tauri. The [Frontend Configuration guide](/start/frontend/) contains common configurations for popular frontend frameworks. Bindings between JavaScript and Rust are available to developers using the `invoke` function in JavaScript and Swift and Kotlin bindings are available for [Tauri Plugins](/develop/plugins/). [TAO](https://github.com/tauri-apps/tao) is responsible for Tauri window creation and [WRY](https://github.com/tauri-apps/wry) is responsible for web view rendering. These are libraries maintained by Tauri and can be consumed directly if deeper system integration is required outside of what Tauri exposes. In addition, Tauri maintains a number of plugins to extend what core Tauri exposes. You can find those plugins alongside those provided by the community in the [Plugins section](/plugin/).

# Create a Project

One thing that makes Tauri so flexible is its ability to work with virtually any frontend framework. We’ve created the [`create-tauri-app`](https://github.com/tauri-apps/create-tauri-app) utility to help you create a new Tauri project using one of the officially maintained framework templates. `create-tauri-app` currently includes templates for vanilla (HTML, CSS and JavaScript without a framework), [Vue.js](https://vuejs.org), [Svelte](https://svelte.dev), [React](https://reactjs.org/), [SolidJS](https://www.solidjs.com/), [Angular](https://angular.io/), [Preact](https://preactjs.com/), [Yew](https://yew.rs/), [Leptos](https://github.com/leptos-rs/leptos), and [Sycamore](https://sycamore.dev/). You can also find or add your own community templates and frameworks in the [Awesome Tauri repo](https://github.com/tauri-apps/awesome-tauri). Alternatively, you can [add Tauri to an existing project](#manual-setup-tauri-cli) to quickly turn your existing codebase into a Tauri app. ## Using `create-tauri-app` To get started using `create-tauri-app` run one of the below commands in the folder you’d like to set up your project. If you’re not sure which command to use we recommend the Bash command on Linux and macOS and the PowerShell command on Windows. * Bash 
  ```sh
  sh <(curl https://create.tauri.app/sh)
  ```
 * PowerShell 
  ```sh
  irm https://create.tauri.app/ps | iex
  ```
 * Fish 
  ```sh
  sh (curl -sSL https://create.tauri.app/sh | psub)
  ```
 * npm 
  ```sh
  npm create tauri-app@latest
  ```
 * Yarn 
  ```sh
  yarn create tauri-app
  ```
 * pnpm 
  ```sh
  pnpm create tauri-app
  ```
 * deno 
  ```sh
  deno run -A npm:create-tauri-app
  ```
 * bun 
  ```sh
  bun create tauri-app
  ```
 * Cargo 
  ```sh
  cargo install create-tauri-app --locked
  cargo create-tauri-app
  ```
 Follow along with the prompts to choose your project name, frontend language, package manager, and frontend framework, and frontend framework options if applicable. #### Scaffold a new project 1. Choose a name and a bundle identifier (unique-id for your app): 
   ```plaintext
   ? Project name (tauri-app) ›
   ? Identifier (com.tauri-app.app) ›
   ```
 2. Select a flavor for your frontend. First the language: 
   ```plaintext
   ? Choose which language to use for your frontend ›
   Rust  (cargo)
   TypeScript / JavaScript  (pnpm, yarn, npm, bun)
   .NET  (dotnet)
   ```
 3. Select a package manager (if there are multiple available): Options for **TypeScript / JavaScript**: 
   ```plaintext
   ? Choose your package manager ›
   pnpm
   yarn
   npm
   bun
   ```
 4. Select a UI Template and flavor (if there are multiple available): Options for **Rust**: 
   ```plaintext
   ? Choose your UI template ›
   Vanilla
   Yew
   Leptos
   Sycamore
   ```
 Options for **TypeScript / JavaScript**: 
   ```plaintext
   ? Choose your UI template ›
   Vanilla
   Vue
   Svelte
   React
   Solid
   Angular
   Preact


   ? Choose your UI flavor ›
   TypeScript
   JavaScript
   ```
 Options for **.NET**: 
   ```plaintext
   ? Choose your UI template ›
   Blazor  (https://dotnet.microsoft.com/en-us/apps/aspnet/web-apps/blazor/)
   ```
 Once completed, the utility reports that the template has been created and displays how to run it using the configured package manager. If it detects missing dependencies on your system, it prints a list of packages and prompts how to install them. #### Start the development server After `create-tauri-app` has completed, you can navigate into your project’s folder, install dependencies, and then use the [Tauri CLI](/reference/cli/) to start the development server: * npm 
  ```sh
  cd tauri-app
  npm install
  npm run tauri dev
  ```
 * yarn 
  ```sh
  cd tauri-app
  yarn install
  yarn tauri dev
  ```
 * pnpm 
  ```sh
  cd tauri-app
  pnpm install
  pnpm tauri dev
  ```
 * deno 
  ```sh
  cd tauri-app
  deno install
  deno task tauri dev
  ```
 * bun 
  ```sh
  cd tauri-app
  bun install
  bun tauri dev
  ```
 * cargo 
  ```sh
  cd tauri-app
  cargo install tauri-cli --version "^2.0.0" --locked
  cargo tauri dev
  ```
 You’ll now see a new window open with your app running. **Congratulations!** You’ve made your Tauri app! 🚀 ## Manual Setup (Tauri CLI) If you already have an existing frontend or prefer to set it up yourself, you can use the Tauri CLI to initialize the backend for your project separately. Note The following example assumes you are creating a new project. If you’ve already initialized the frontend of your application, you can skip the first step. 1. Create a new directory for your project and initialize the frontend. You can use plain HTML, CSS, and JavaScript, or any framework you prefer such as Next.js, Nuxt, Svelte, Yew, or Leptos. You just need a way of serving the app in your browser. Just as an example, this is how you would set up a simple Vite app: * npm 
     ```sh
     mkdir tauri-app
     cd tauri-app
     npm create vite@latest .
     ```
 * yarn 
     ```sh
     mkdir tauri-app
     cd tauri-app
     yarn create vite .
     ```
 * pnpm 
     ```sh
     mkdir tauri-app
     cd tauri-app
     pnpm create vite .
     ```
 * deno 
     ```sh
     mkdir tauri-app
     cd tauri-app
     deno run -A npm:create-vite .
     ```
 * bun 
     ```sh
     mkdir tauri-app
     cd tauri-app
     bun create vite
     ```
 2. Then, install Tauri’s CLI tool using your package manager of choice. If you are using `cargo` to install the Tauri CLI, you will have to install it globally. * npm 
     ```sh
     npm install -D @tauri-apps/cli@latest
     ```
 * yarn 
     ```sh
     yarn add -D @tauri-apps/cli@latest
     ```
 * pnpm 
     ```sh
     pnpm add -D @tauri-apps/cli@latest
     ```
 * deno 
     ```sh
     deno add -D npm:@tauri-apps/cli@latest
     ```
 * bun 
     ```sh
     bun add -D @tauri-apps/cli@latest
     ```
 * cargo 
     ```sh
     cargo install tauri-cli --version "^2.0.0" --locked
     ```
 3. Determine the URL of your frontend development server. This is the URL that Tauri will use to load your content. For example, if you are using Vite, the default URL is `http://localhost:5173`. 4. In your project directory, initialize Tauri: * npm 
     ```sh
     npx tauri init
     ```
 * yarn 
     ```sh
     yarn tauri init
     ```
 * pnpm 
     ```sh
     pnpm tauri init
     ```
 * deno 
     ```sh
     deno task tauri init
     ```
 * bun 
     ```sh
     bun tauri init
     ```
 * cargo 
     ```sh
     cargo tauri init
     ```
 After running the command it will display a prompt asking you for different options: 
   ```sh
   ✔ What is your app name? tauri-app
   ✔ What should the window title be? tauri-app
   ✔ Where are your web assets located? ..
   ✔ What is the url of your dev server? http://localhost:5173
   ✔ What is your frontend dev command? pnpm run dev
   ✔ What is your frontend build command? pnpm run build
   ```
 This will create a `src-tauri` directory in your project with the necessary Tauri configuration files. 5. Configure the `server.watch.ignored` option in `vite.config.ts` to prevent Vite from watching the `src-tauri` directory: vite.config.ts 
   ```js
   import { defineConfig } from "vite";


   export default defineConfig({
     server: {
       watch: {
         ignored: ["**/src-tauri/**"],
       },
     },
   });
   ```
 6. Verify your Tauri app is working by running the development server: * npm 
     ```sh
     npx tauri dev
     ```
 * yarn 
     ```sh
     yarn tauri dev
     ```
 * pnpm 
     ```sh
     pnpm tauri dev
     ```
 * deno 
     ```sh
     deno task tauri dev
     ```
 * bun 
     ```sh
     bun tauri dev
     ```
 * cargo 
     ```sh
     cargo tauri dev
     ```
 This command will compile the Rust code and open a window with your web content. **Congratulations!** You’ve created a new Tauri project using the Tauri CLI! 🚀 ## Next Steps * [Learn about the project layout and what each file does](/start/project-structure/) * [Add and Configure a Frontend Framework](/start/frontend/) * [Tauri Command Line Interface (CLI) Reference](/reference/cli/) * [Learn how to develop your Tauri app](/develop/) * [Discover additional features to extend Tauri](/plugin/)

# Frontend Configuration

Tauri is frontend agnostic and supports most frontend frameworks out of the box. However, sometimes a framework needs a bit of extra configuration to integrate with Tauri. Below is a list of frameworks and their recommended configurations. If a framework is not listed then it may work with Tauri with no additional configuration needed or it could have not been documented yet. Any contributions to add a framework that may require additional configuration are welcome to help others in the Tauri community. ## Configuration Checklist Conceptually Tauri acts as a static web host. You need to provide Tauri with a folder containing some mix of HTML, CSS, JavaScript and possibly WASM that can be served to the webview Tauri provides. Below is a checklist of common scenarios needed to integrate a frontend with Tauri: * Use static site generation (SSG), single-page applications (SPA), or classic multi-page apps (MPA). Tauri does not natively support server based alternatives (such as SSR). * For mobile development, a development server of some kind is necessary that can host the frontend on your internal IP. * Use a proper client-server relationship between your app and your APIs (no hybrid solutions with SSR). ## JavaScript For most projects we recommend [Vite](https://vitejs.dev/) for SPA frameworks such as React, Vue, Svelte, and Solid, but also for plain JavaScript or TypeScript projects. Most other guides listed here show how to use Meta-Frameworks as they are typically designed for SSR and therefore require special configuration. [Next.js](/start/frontend/nextjs/) [Nuxt](/start/frontend/nuxt/) [Qwik](/start/frontend/qwik/) [SvelteKit](/start/frontend/sveltekit/) [Vite (recommended)](/start/frontend/vite/) ## Rust [Leptos](/start/frontend/leptos/) [Trunk](/start/frontend/trunk/)

# Leptos

Leptos is a Rust based web framework. You can read more about Leptos on their [official website](https://leptos.dev/). This guide is accurate as of Leptos version 0.6. ## Checklist * Use SSG, Tauri doesn’t officially support server based solutions. * Use `serve.ws_protocol = "ws"` so that the hot-reload websocket can connect properly for mobile development. * Enable `withGlobalTauri` to ensure that Tauri APIs are available in the `window.__TAURI__` variable and can be imported using `wasm-bindgen`. ## Example Configuration 1. ##### Update Tauri configuration src-tauri/tauri.conf.json 
   ```json
   {
     "build": {
       "beforeDevCommand": "trunk serve",
       "devUrl": "http://localhost:1420",
       "beforeBuildCommand": "trunk build",
       "frontendDist": "../dist"
     },
     "app": {
       "withGlobalTauri": true
     }
   }
   ```
 2. ##### Update Trunk configuration Trunk.toml 
   ```toml
   [build]
   target = "./index.html"


   [watch]
   ignore = ["./src-tauri"]


   [serve]
   port = 1420
   open = false
   ws_protocol = "ws"
   ```

# Next.js

Next.js is a meta framework for React. Learn more about Next.js at <https://nextjs.org>. This guide is accurate as of Next.js 14.2.3. ## Checklist * Use static exports by setting `output: 'export'`. Tauri doesn’t support server-based solutions. * Use the `out` directory as `frontendDist` in `tauri.conf.json`. ## Example Configuration 1. ##### Update Tauri configuration * npm src-tauri/tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "npm run dev",
         "beforeBuildCommand": "npm run build",
         "devUrl": "http://localhost:3000",
         "frontendDist": "../out"
       }
     }
     ```
 * yarn src-tauri/tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "yarn dev",
         "beforeBuildCommand": "yarn build",
         "devUrl": "http://localhost:3000",
         "frontendDist": "../out"
       }
     }
     ```
 * pnpm src-tauri/tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "pnpm dev",
         "beforeBuildCommand": "pnpm build",
         "devUrl": "http://localhost:3000",
         "frontendDist": "../out"
       }
     }
     ```
 * deno src-tauri/tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "deno task dev",
         "beforeBuildCommand": "deno task build",
         "devUrl": "http://localhost:3000",
         "frontendDist": "../out"
       }
     }
     ```
 2. ##### Update Next.js configuration next.config.mjs 
   ```ts
   const isProd = process.env.NODE_ENV === 'production';


   const internalHost = process.env.TAURI_DEV_HOST || 'localhost';


   /** @type {import('next').NextConfig} */
   const nextConfig = {
     // Ensure Next.js uses SSG instead of SSR
     // https://nextjs.org/docs/pages/building-your-application/deploying/static-exports
     output: 'export',
     // Note: This feature is required to use the Next.js Image component in SSG mode.
     // See https://nextjs.org/docs/messages/export-image-api for different workarounds.
     images: {
       unoptimized: true,
     },
     // Configure assetPrefix or else the server won't properly resolve your assets.
     assetPrefix: isProd ? undefined : `http://${internalHost}:3000`,
   };


   export default nextConfig;
   ```
 3. ##### Update package.json configuration 
   ```json
   "scripts": {
     "dev": "next dev",
     "build": "next build",
     "start": "next start",
     "lint": "next lint",
     "tauri": "tauri"
   }
   ```

# Nuxt

Nuxt is a meta framework for Vue. Learn more about Nuxt at <https://nuxt.com>. This guide is accurate as of Nuxt 4.2. ## Checklist * Use SSG by setting `ssr: false`. Tauri doesn’t support server based solutions. * Use default `../dist` as `frontendDist` in `tauri.conf.json`. * Compile using `nuxi build`. * (Optional): Disable telemetry by setting `telemetry: false` in `nuxt.config.ts`. ## Example Configuration 1. ##### Update Tauri configuration * npm tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "npm run dev",
         "beforeBuildCommand": "npm run generate",
         "devUrl": "http://localhost:3000",
         "frontendDist": "../dist"
       }
     }
     ```
 * yarn tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "yarn dev",
         "beforeBuildCommand": "yarn generate",
         "devUrl": "http://localhost:3000",
         "frontendDist": "../dist"
       }
     }
     ```
 * pnpm tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "pnpm dev",
         "beforeBuildCommand": "pnpm generate",
         "devUrl": "http://localhost:3000",
         "frontendDist": "../dist"
       }
     }
     ```
 * deno tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "deno task dev",
         "beforeBuildCommand": "deno task generate",
         "devUrl": "http://localhost:3000",
         "frontendDist": "../dist"
       }
     }
     ```
 2. ##### Update Nuxt configuration 
   ```ts
   export default defineNuxtConfig({
     compatibilityDate: '2025-05-15',
     // (optional) Enable the Nuxt devtools
     devtools: { enabled: true },
     // Enable SSG
     ssr: false,
     // Enables the development server to be discoverable by other devices when running on iOS physical devices
     devServer: {
       host: '0',
     },
     vite: {
       // Better support for Tauri CLI output
       clearScreen: false,
       // Enable environment variables
       // Additional environment variables can be found at
       // https://v2.tauri.app/reference/environment-variables/
       envPrefix: ['VITE_', 'TAURI_'],
       server: {
         // Tauri requires a consistent port
         strictPort: true,
       },
     },
     // Avoids error [unhandledRejection] EMFILE: too many open files, watch
     ignore: ['**/src-tauri/**'],
   });
   ```

# Qwik

This guide will walk you through creating your Tauri app using the Qwik web framework. Learn more about Qwik at <https://qwik.dev>. ## Checklist * Use [SSG](https://qwik.dev/docs/guides/static-site-generation/). Tauri doesn’t support server-based solutions. * Use `dist/` as `frontendDist` in `tauri.conf.json`. ## Example Configuration 1. ##### Create a new Qwik app * npm 
     ```sh
     npm create qwik@latest
     cd <PROJECT>
     ```
 * yarn 
     ```sh
     yarn create qwik@latest
     cd <PROJECT>
     ```
 * pnpm 
     ```sh
     pnpm create qwik@latest
     cd <PROJECT>
     ```
 * deno 
     ```sh
     deno run -A npm:create-qwik@latest
     cd <PROJECT>
     ```
 2. ##### Install the `static adapter` * npm 
     ```sh
     npm run qwik add static
     ```
 * yarn 
     ```sh
     yarn qwik add static
     ```
 * pnpm 
     ```sh
     pnpm qwik add static
     ```
 * deno 
     ```sh
     deno task qwik add static
     ```
 3. ##### Add the Tauri CLI to your project * npm 
     ```sh
     npm install -D @tauri-apps/cli@latest
     ```
 * yarn 
     ```sh
     yarn add -D @tauri-apps/cli@latest
     ```
 * pnpm 
     ```sh
     pnpm add -D @tauri-apps/cli@latest
     ```
 * deno 
     ```sh
     deno add -D npm:@tauri-apps/cli@latest
     ```
 4. ##### Initiate a new Tauri project * npm 
     ```sh
     npm run tauri init
     ```
 * yarn 
     ```sh
     yarn tauri init
     ```
 * pnpm 
     ```sh
     pnpm tauri init
     ```
 * deno 
     ```sh
     deno task tauri init
     ```
 5. ##### Tauri configuration * npm tauri.conf.json 
     ```json
     {
       "build": {
         "devUrl": "http://localhost:5173"
         "frontendDist": "../dist",
         "beforeDevCommand": "npm run dev",
         "beforeBuildCommand": "npm run build"
       }
     }
     ```
 * yarn tauri.conf.json 
     ```json
     {
       "build": {
         "devUrl": "http://localhost:5173"
         "frontendDist": "../dist",
         "beforeDevCommand": "yarn dev",
         "beforeBuildCommand": "yarn build"
       }
     }
     ```
 * pnpm tauri.conf.json 
     ```json
     {
       "build": {
         "devUrl": "http://localhost:5173"
         "frontendDist": "../dist",
         "beforeDevCommand": "pnpm dev",
         "beforeBuildCommand": "pnpm build"
       }
     }
     ```
 * deno tauri.conf.json 
     ```json
     {
       "build": {
         "devUrl": "http://localhost:5173"
         "frontendDist": "../dist",
         "beforeDevCommand": "deno task dev",
         "beforeBuildCommand": "deno task build"
       }
     }
     ```
 6. ##### Start your `tauri` app * npm 
     ```sh
     npm run tauri dev
     ```
 * yarn 
     ```sh
     yarn tauri dev
     ```
 * pnpm 
     ```sh
     pnpm tauri dev
     ```
 * deno 
     ```sh
     deno task tauri dev
     ```

# SvelteKit

SvelteKit is a meta framework for Svelte. Learn more about SvelteKit at <https://svelte.dev/>. This guide is accurate as of SvelteKit 2.20.4 / Svelte 5.25.8. ## Checklist * Use [SSG](https://svelte.dev/docs/kit/adapter-static) and [SPA](https://svelte.dev/docs/kit/single-page-apps) via `static-adapter`. Tauri doesn’t support server-based solutions. * If using SSG **with prerendering**, be aware that `load` functions will not have access to tauri APIs during the build process of your app. Using SPA mode (without prerendering) is recommended since the load functions will only run in the webview with access to tauri APIs. * Use `build/` as `frontendDist` in `tauri.conf.json`. ## Example Configuration 1. ##### Install `@sveltejs/adapter-static` * npm 
     ```sh
     npm install --save-dev @sveltejs/adapter-static
     ```
 * yarn 
     ```sh
     yarn add -D @sveltejs/adapter-static
     ```
 * pnpm 
     ```sh
     pnpm add -D @sveltejs/adapter-static
     ```
 * deno 
     ```sh
     deno add -D npm:@sveltejs/adapter-static
     ```
 2. ##### Update Tauri configuration * npm tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "npm run dev",
         "beforeBuildCommand": "npm run build",
         "devUrl": "http://localhost:5173",
         "frontendDist": "../build"
       }
     }
     ```
 * yarn tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "yarn dev",
         "beforeBuildCommand": "yarn build",
         "devUrl": "http://localhost:5173",
         "frontendDist": "../build"
       }
     }
     ```
 * pnpm tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "pnpm dev",
         "beforeBuildCommand": "pnpm build",
         "devUrl": "http://localhost:5173",
         "frontendDist": "../build"
       }
     }
     ```
 * deno tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "deno task dev",
         "beforeBuildCommand": "deno task build",
         "devUrl": "http://localhost:5173",
         "frontendDist": "../build"
       }
     }
     ```
 3. ##### Update SvelteKit configuration: svelte.config.js 
   ```js
   import adapter from '@sveltejs/adapter-static';
   import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';


   /** @type {import('@sveltejs/kit').Config} */
   const config = {
     // Consult https://svelte.dev/docs/kit/integrations#preprocessors
     // for more information about preprocessors
     preprocess: vitePreprocess(),


     kit: {
       adapter: adapter({
         fallback: 'index.html',
       }),
     },
   };


   export default config;
   ```
 4. ##### Disable SSR Lastly, we need to disable SSR by adding a root `+layout.ts` file (or `+layout.js` if you are not using TypeScript) with these contents: src/routes/+layout.ts 
   ```ts
   export const ssr = false;
   ```
 Note that `static-adapter` doesn’t require you to disable SSR for the whole app but it makes it possible to use APIs that depend on the global window object (like Tauri’s API) without [Client-side checks](https://svelte.dev/docs/kit/faq#how-do-i-use-x-with-sveltekit-how-do-i-use-a-client-side-only-library-that-depends-on-document-or-window). Furthermore, if you prefer Static Site Generation (SSG) over Single-Page Application (SPA) mode, you can change the adapter configurations and `+layout.ts` according to the [adapter docs](https://svelte.dev/docs/kit/adapter-static).

# Trunk

Trunk is a WASM web application bundler for Rust. Learn more about Trunk at <https://trunk-rs.github.io/trunk/>. This guide is accurate as of Trunk 0.17.5. ## Checklist * Use SSG, Tauri doesn’t officially support server based solutions. * Use `serve.ws_protocol = "ws"` so that the hot-reload websocket can connect properly for mobile development. * Enable `withGlobalTauri` to ensure that Tauri APIs are available in the `window.__TAURI__` variable and can be imported using `wasm-bindgen`. ## Example Configuration 1. ##### Update Tauri configuration tauri.conf.json 
   ```json
   {
     "build": {
       "beforeDevCommand": "trunk serve",
       "beforeBuildCommand": "trunk build",
       "devUrl": "http://localhost:8080",
       "frontendDist": "../dist"
     },
     "app": {
       "withGlobalTauri": true
     }
   }
   ```
 2. ##### Update Trunk configuration Trunk.toml 
   ```toml
   [watch]
   ignore = ["./src-tauri"]


   [serve]
   ws_protocol = "ws"
   ```

# Vite

Vite is a build tool that aims to provide a faster and leaner development experience for modern web projects. This guide is accurate as of Vite 8. ## Checklist * Use `../dist` as `frontendDist` in `src-tauri/tauri.conf.json`. * Use `process.env.TAURI_DEV_HOST` as the development server host IP when set to run on iOS physical devices. ## Example configuration 1. ##### Update Tauri configuration Assuming you have the following `dev` and `build` scripts in your `package.json`: 
   ```json
   {
     "scripts": {
       "dev": "vite",
       "build": "tsc && vite build",
       "preview": "vite preview",
       "tauri": "tauri"
     }
   }
   ```
 You can configure the Tauri CLI to use your Vite development server and dist folder along with the hooks to automatically run the Vite scripts: * npm tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "npm run dev",
         "beforeBuildCommand": "npm run build",
         "devUrl": "http://localhost:5173",
         "frontendDist": "../dist"
       }
     }
     ```
 * yarn tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "yarn dev",
         "beforeBuildCommand": "yarn build",
         "devUrl": "http://localhost:5173",
         "frontendDist": "../dist"
       }
     }
     ```
 * pnpm tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "pnpm dev",
         "beforeBuildCommand": "pnpm build",
         "devUrl": "http://localhost:5173",
         "frontendDist": "../dist"
       }
     }
     ```
 * deno tauri.conf.json 
     ```json
     {
       "build": {
         "beforeDevCommand": "deno task dev",
         "beforeBuildCommand": "deno task build",
         "devUrl": "http://localhost:5173",
         "frontendDist": "../dist"
       }
     }
     ```
 2. ##### Update Vite configuration: vite.config.js 
   ```js
   import { defineConfig } from 'vite';


   const host = process.env.TAURI_DEV_HOST;


   export default defineConfig({
     // prevent vite from obscuring rust errors
     clearScreen: false,
     server: {
       // make sure this port matches the devUrl port in tauri.conf.json file
       port: 5173,
       // Tauri expects a fixed port, fail if that port is not available
       strictPort: true,
       // if the host Tauri is expecting is set, use it
       host: host || false,
       hmr: host
         ? {
             protocol: 'ws',
             host,
             port: 1421,
           }
         : undefined,


       watch: {
         // tell vite to ignore watching `src-tauri`
         ignored: ['**/src-tauri/**'],
       },
     },
     // Env variables starting with the item of `envPrefix` will be exposed in tauri's source code through `import.meta.env`.
     envPrefix: ['VITE_', 'TAURI_ENV_*'],
     build: {
       // Tauri uses Chromium on Windows and WebKit on macOS and Linux
       target:
         process.env.TAURI_ENV_PLATFORM == 'windows'
           ? 'chrome105'
           : 'safari13',
       // don't minify for debug builds
       minify: !process.env.TAURI_ENV_DEBUG,
       // produce sourcemaps for debug builds
       sourcemap: !!process.env.TAURI_ENV_DEBUG,
     },
   });
   ```

# Upgrade & Migrate

Learn about common scenarios and steps to upgrade from Tauri 1.0 or migrate from another framework. [Upgrade from Tauri 1.0](/start/migrate/from-tauri-1/)Read more about the updates you need to make to a version 1 project in order to upgrade to version 2. [Migrate from Tauri 2.0 beta](/start/migrate/from-tauri-2-beta/)Read more about the updates required for the 2.0 beta project to upgrade to 2.0.

# Upgrade from Tauri 1.0

This guide walks you through upgrading your Tauri 1.0 application to Tauri 2.0. ## Preparing for Mobile The mobile interface of Tauri requires your project to output a shared library. If you are targeting mobile for your existing application, you must change your crate to produce that kind of artifact along with the desktop executable. 1. Change the Cargo manifest to produce the library. Append the following block: src-tauri/Cargo.toml 
```toml
[lib]
name = "app_lib"
crate-type = ["staticlib", "cdylib", "rlib"]
```
 2. Rename `src-tauri/src/main.rs` to `src-tauri/src/lib.rs`. This file will be shared by both desktop and mobile targets. 3. Rename the `main` function header in `lib.rs` to the following: src-tauri/src/lib.rs 
```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // your code here
}
```
 The `tauri::mobile_entry_point` macro prepares your function to be executed on mobile. 4. Recreate the `main.rs` file calling the shared run function: src-tauri/src/main.rs 
```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]


fn main() {
  app_lib::run();
}
```
 ## Automated Migration Danger This command is not a substitute for this guide! Please read the *whole* page regardless of whether you chose to use the command. The Tauri v2 CLI includes a `migrate` command that automates most of the process and helps you finish the migration: * npm 
  ```sh
  npm install @tauri-apps/cli@latest
  npm run tauri migrate
  ```
 * yarn 
  ```sh
  yarn upgrade @tauri-apps/cli@latest
  yarn tauri migrate
  ```
 * pnpm 
  ```sh
  pnpm update @tauri-apps/cli@latest
  pnpm tauri migrate
  ```
 * cargo 
  ```sh
  cargo install tauri-cli --version "^2.0.0" --locked
  cargo tauri migrate
  ```
 Learn more about the `migrate` command in the [Command Line Interface reference](/reference/cli/#migrate) ## Summary of Changes Below is a summary of the changes from Tauri 1.0 to Tauri 2.0: ### Tauri Configuration * `package > productName` and `package > version` moved to top-level object. * the binary name is no longer renamed to match `productName` automatically, so you must add a `mainBinaryName` string to the top-level object matching `productName`. * `package` removed. * `tauri` key renamed to `app`. * `tauri > allowlist` removed. Refer to [Migrate Permissions](#migrate-permissions). * `tauri > allowlist > protocol > assetScope` moved to `app > security > assetProtocol > scope`. See [Asset protocol scope](/security/asset-protocol/) for `enable`, glob patterns, `requireLiteralLeadingDot`, and dynamic paths. * `tauri > cli` moved to `plugins > cli`. * `tauri > windows > fileDropEnabled` renamed to `app > windows > dragDropEnabled`. * `tauri > updater > active` removed. * `tauri > updater > dialog` removed. * `tauri > updater` moved to `plugins > updater`. * `bundle > createUpdaterArtifacts` added, must be set when using the app updater. * set it to `v1Compatible` when upgrading from v1 apps that were already distributed. See the [updater guide](/plugin/updater/) for more information. * `tauri > systemTray` renamed to `app > trayIcon`. * `tauri > pattern` moved to `app > security > pattern`. * `tauri > bundle` moved top-level. * `tauri > bundle > identifier` moved to top-level object. * `tauri > bundle > dmg` moved to `bundle > macOS > dmg` * `tauri > bundle > deb` moved to `bundle > linux > deb` * `tauri > bundle > appimage` moved to `bundle > linux > appimage` * `tauri > bundle > macOS > license` removed, use `bundle > licenseFile` instead. * `tauri > bundle > windows > wix > license` removed, use `bundle > licenseFile` instead. * `tauri > bundle > windows > nsis > license` removed, use `bundle > licenseFile` instead. * `tauri > bundle > windows > webviewFixedRuntimePath` removed, use `bundle > windows > webviewInstallMode` instead. * `build > withGlobalTauri` moved to `app > withGlobalTauri`. * `build > distDir` renamed to `frontendDist`. * `build > devPath` renamed to `devUrl`. [Tauri 2.0 Configuration API reference](/reference/config/) ### New Cargo Features * linux-protocol-body: Enables custom protocol request body parsing, allowing the IPC to use it. Requires webkit2gtk 2.40. ### Removed Cargo Features * reqwest-client: reqwest is now the only supported client. * reqwest-native-tls-vendored: use `native-tls-vendored` instead. * process-command-api: use the `shell` plugin instead (see instructions in the following section). * shell-open-api: use the `shell` plugin instead (see instructions in the following section). * windows7-compat: moved to the `notification` plugin. * updater: Updater is now a plugin. * linux-protocol-headers: Now enabled by default since we upgraded our minimum webkit2gtk version. * system-tray: renamed to `tray-icon`. ### Rust Crate Changes * `api` module removed. Each API module can be found in a Tauri plugin. * `api::dialog` module removed. Use `tauri-plugin-dialog` instead. [Migration](#migrate-to-dialog-plugin) * `api::file` module removed. Use Rust’s [`std::fs`](https://doc.rust-lang.org/std/fs/) instead. * `api::http` module removed. Use `tauri-plugin-http` instead. [Migration](#migrate-to-http-plugin) * `api::ip` module rewritten and moved to `tauri::ipc`. Check out the new APIs, specially `tauri::ipc::Channel`. * `api::path` module functions and `tauri::PathResolved` moved to `tauri::Manager::path`. [Migration](#migrate-path-to-tauri-manager) * `api::process::Command`, `tauri::api::shell` and `tauri::Manager::shell_scope` APIs removed. Use `tauri-plugin-shell` instead. [Migration](#migrate-to-shell-plugin) * `api::process::current_binary` and `tauri::api::process::restart` moved to `tauri::process`. * `api::version` module has been removed. Use the [semver crate](https://docs.rs/semver/latest/semver/) instead. * `App::clipboard_manager` and `AppHandle::clipboard_manager` removed. Use `tauri-plugin-clipboard` instead. [Migration](#migrate-to-clipboard-plugin) * `App::get_cli_matches` removed. Use `tauri-plugin-cli` instead. [Migration](#migrate-to-cli-plugin) * `App::global_shortcut_manager` and `AppHandle::global_shortcut_manager` removed. Use `tauri-plugin-global-shortcut` instead. [Migration](#migrate-to-global-shortcut-plugin) * `Manager::fs_scope` removed. The file system scope can be accessed via `tauri_plugin_fs::FsExt`. * `Plugin::PluginApi` now receives a plugin configuration as a second argument. * `Plugin::setup_with_config` removed. Use the updated `tauri::Plugin::PluginApi` instead. * `scope::ipc::RemoteDomainAccessScope::enable_tauri_api` and `scope::ipc::RemoteDomainAccessScope::enables_tauri_api` removed. Enable each core plugin individually via `scope::ipc::RemoteDomainAccessScope::add_plugin` instead. * `scope::IpcScope` removed, use `scope::ipc::Scope` instead. * `scope::FsScope`, `scope::GlobPattern` and `scope::FsScopeEvent` removed, use `scope::fs::Scope`, `scope::fs::Pattern` and `scope::fs::Event` respectively. * `updater` module removed. Use `tauri-plugin-updater` instead. [Migration](#migrate-to-updater-plugin) * `Env.args` field has been removed, use `Env.args_os` field instead. * `Menu`, `MenuEvent`, `CustomMenuItem`, `Submenu`, `WindowMenuEvent`, `MenuItem` and `Builder::on_menu_event` APIs removed. [Migration](#migrate-to-menu) * `SystemTray`, `SystemTrayHandle`, `SystemTrayMenu`, `SystemTrayMenuItemHandle`, `SystemTraySubmenu`, `MenuEntry` and `SystemTrayMenuItem` APIs removed. [Migration](#migrate-to-tray-icon-module) ### JavaScript API Changes The `@tauri-apps/api` package no longer provides non-core modules. Only the previous `tauri` (now `core`), `path`, `event` and `window` modules are exported. All others have been moved to plugins. * `@tauri-apps/api/tauri` module renamed to `@tauri-apps/api/core`. [Migration](#migrate-to-core-module) * `@tauri-apps/api/cli` module removed. Use `@tauri-apps/plugin-cli` instead. [Migration](#migrate-to-cli-plugin) * `@tauri-apps/api/clipboard` module removed. Use `@tauri-apps/plugin-clipboard` instead. [Migration](#migrate-to-clipboard-plugin) * `@tauri-apps/api/dialog` module removed. Use `@tauri-apps/plugin-dialog` instead. [Migration](#migrate-to-dialog-plugin) * `@tauri-apps/api/fs` module removed. Use `@tauri-apps/plugin-fs` instead. [Migration](#migrate-to-file-system-plugin) * `@tauri-apps/api/global-shortcut` module removed. Use `@tauri-apps/plugin-global-shortcut` instead. [Migration](#migrate-to-global-shortcut-plugin) * `@tauri-apps/api/http` module removed. Use `@tauri-apps/plugin-http` instead. [Migration](#migrate-to-http-plugin) * `@tauri-apps/api/os` module removed. Use `@tauri-apps/plugin-os` instead. [Migration](#migrate-to-os-plugin) * `@tauri-apps/api/notification` module removed. Use `@tauri-apps/plugin-notification` instead. [Migration](#migrate-to-notification-plugin) * `@tauri-apps/api/process` module removed. Use `@tauri-apps/plugin-process` instead. [Migration](#migrate-to-process-plugin) * `@tauri-apps/api/shell` module removed. Use `@tauri-apps/plugin-shell` instead. [Migration](#migrate-to-shell-plugin) * `@tauri-apps/api/updater` module removed. Use `@tauri-apps/plugin-updater` instead [Migration](#migrate-to-updater-plugin) * `@tauri-apps/api/window` module renamed to `@tauri-apps/api/webviewWindow`. [Migration](#migrate-to-new-window-api) The v1 plugins are now published as `@tauri-apps/plugin-<plugin-name>`. Previously they were available from git as `tauri-plugin-<plugin-name>-api`. ### Environment Variables Changes Most of the environment variables read and written by the Tauri CLI were renamed for consistency and prevention of mistakes: * `TAURI_PRIVATE_KEY` -> `TAURI_SIGNING_PRIVATE_KEY` * `TAURI_KEY_PASSWORD` -> `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` * `TAURI_SKIP_DEVSERVER_CHECK` -> `TAURI_CLI_NO_DEV_SERVER_WAIT` * `TAURI_DEV_SERVER_PORT` -> `TAURI_CLI_PORT` * `TAURI_PATH_DEPTH` -> `TAURI_CLI_CONFIG_DEPTH` * `TAURI_FIPS_COMPLIANT` -> `TAURI_BUNDLER_WIX_FIPS_COMPLIANT` * `TAURI_DEV_WATCHER_IGNORE_FILE` -> `TAURI_CLI_WATCHER_IGNORE_FILENAME` * `TAURI_TRAY` -> `TAURI_LINUX_AYATANA_APPINDICATOR` * `TAURI_APPLE_DEVELOPMENT_TEAM` -> `APPLE_DEVELOPMENT_TEAM` * `TAURI_PLATFORM` -> `TAURI_ENV_PLATFORM` * `TAURI_ARCH` -> `TAURI_ENV_ARCH` * `TAURI_FAMILY` -> `TAURI_ENV_FAMILY` * `TAURI_PLATFORM_VERSION` -> `TAURI_ENV_PLATFORM_VERSION` * `TAURI_PLATFORM_TYPE` -> `TAURI_ENV_PLATFORM_TYPE` * `TAURI_DEBUG` -> `TAURI_ENV_DEBUG` ### Event System The event system was redesigned to be easier to use. Instead of relying on the source of the event, it now has a simpler implementation that relies on event targets. * The `emit` function now emits the event to all event listeners. * Added a new `emit_to`/`emitTo` function to trigger an event to a specific target. * `emit_filter` now filters based on [`EventTarget`](https://docs.rs/tauri/2.0.0/tauri/event/enum.EventTarget.html) instead of a window. * Renamed `listen_global` to `listen_any`. It now listens to all events regardless of their filters and targets. * JavaScript: `event.listen()` behaves similar to `listen_any`. It now listens to all events regardless of their filters and targets, unless a target is set in the `Options`. * JavaScript: `WebviewWindow.listen` etc. only listen to events emitted to the respective `EventTarget`. ### Multiwebview support Tauri v2 introduces multiwebview support currently behind an `unstable` feature flag. In order to support it, we renamed the Rust `Window` type to `WebviewWindow` and the Manager `get_window` function to `get_webview_window`. The `WebviewWindow` JS API type is now re-exported from `@tauri-apps/api/webviewWindow` instead of `@tauri-apps/api/window`. ### New origin URL on Windows On Windows the frontend files in production apps are now hosted on `http://tauri.localhost` instead of `https://tauri.localhost`. Because of this IndexedDB, LocalStorage and Cookies will be reset unless `dangerousUseHttpScheme` was used in v1. To prevent this you can set `app > windows > useHttpsScheme` to `true` or use `WebviewWindowBuilder::use_https_scheme` to keep using the `https` scheme. ## Detailed Migration Steps Common scenarios you may encounter when migrating your Tauri 1.0 app to Tauri 2.0. ### Migrate to Core Module The `@tauri-apps/api/tauri` module was renamed to `@tauri-apps/api/core`. Simply rename the module import: 
```diff
import { invoke } from "@tauri-apps/api/tauri"
import { invoke } from "@tauri-apps/api/core"
```
 ### Migrate to CLI Plugin The Rust `App::get_cli_matches` JavaScript `@tauri-apps/api/cli` APIs have been removed. Use the `@tauri-apps/plugin-cli` plugin instead: 1. Add to cargo dependencies: Cargo.toml 
```toml
[dependencies]
tauri-plugin-cli = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_cli::init())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-cli": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { getMatches } from '@tauri-apps/plugin-cli';
  const matches = await getMatches();
  ```
 * Rust 
  ```rust
  fn main() {
      use tauri_plugin_cli::CliExt;
      tauri::Builder::default()
          .plugin(tauri_plugin_cli::init())
          .setup(|app| {
              let cli_matches = app.cli().matches()?;
              Ok(())
          })
  }
  ```
 ### Migrate to Clipboard Plugin The Rust `App::clipboard_manager` and `AppHandle::clipboard_manager` and JavaScript `@tauri-apps/api/clipboard` APIs have been removed. Use the `@tauri-apps/plugin-clipboard-manager` plugin instead: 
```toml
[dependencies]
tauri-plugin-clipboard-manager = "2"
```
 * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_clipboard_manager::init())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-clipboard-manager": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { writeText, readText } from '@tauri-apps/plugin-clipboard-manager';
  await writeText('Tauri is awesome!');
  assert(await readText(), 'Tauri is awesome!');
  ```
 * Rust 
  ```rust
  use tauri_plugin_clipboard::{ClipboardExt, ClipKind};
  tauri::Builder::default()
      .plugin(tauri_plugin_clipboard::init())
      .setup(|app| {
          app.clipboard().write(ClipKind::PlainText {
              label: None,
              text: "Tauri is awesome!".into(),
          })?;
          Ok(())
      })
  ```
 ### Migrate to Dialog Plugin The Rust `tauri::api::dialog` JavaScript `@tauri-apps/api/dialog` APIs have been removed. Use the `@tauri-apps/plugin-dialog` plugin instead: 1. Add to cargo dependencies: Cargo.toml 
```toml
[dependencies]
tauri-plugin-dialog = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_dialog::init())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-dialog": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { save } from '@tauri-apps/plugin-dialog';
  const filePath = await save({
    filters: [
      {
        name: 'Image',
        extensions: ['png', 'jpeg'],
      },
    ],
  });
  ```
 * Rust 
  ```rust
  use tauri_plugin_dialog::DialogExt;
  tauri::Builder::default()
      .plugin(tauri_plugin_dialog::init())
      .setup(|app| {
          app.dialog().file().pick_file(|file_path| {
              // do something with the optional file path here
              // the file path is `None` if the user closed the dialog
          });


          app.dialog().message("Tauri is Awesome!").show();
          Ok(())
       })
  ```
 ### Migrate to File System Plugin The Rust `tauri::api::file` and JavaScript `@tauri-apps/api/fs` APIs have been removed. Use [`std::fs`](https://doc.rust-lang.org/std/fs/) for Rust and the `@tauri-apps/plugin-fs` plugin for JavaScript instead: 1. Add to cargo dependencies: Cargo.toml 
```toml
[dependencies]
tauri-plugin-fs = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_fs::init())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-fs": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { mkdir, BaseDirectory } from '@tauri-apps/plugin-fs';
  await mkdir('db', { baseDir: BaseDirectory.AppLocalData });
  ```
 Some functions and types have been renamed or removed: * `Dir` enum alias removed, use `BaseDirectory`. * `FileEntry`, `FsBinaryFileOption`, `FsDirOptions`, `FsOptions`, `FsTextFileOption` and `BinaryFileContents` interfaces and type aliases have been removed and replaced with new interfaces suited for each function. * `createDir` renamed to `mkdir`. * `readBinaryFile` renamed to `readFile`. * `removeDir` removed and replaced with `remove`. * `removeFile` removed and replaced with `remove`. * `renameFile` removed and replaced with `rename`. * `writeBinaryFile` renamed to `writeFile`. * Rust Use the Rust [`std::fs`](https://doc.rust-lang.org/std/fs/) functions. ### Migrate to Global Shortcut Plugin The Rust `App::global_shortcut_manager` and `AppHandle::global_shortcut_manager` and JavaScript `@tauri-apps/api/global-shortcut` APIs have been removed. Use the `@tauri-apps/plugin-global-shortcut` plugin instead: 1. Add to cargo dependencies: Cargo.toml 
```toml
[dependencies]
[target."cfg(not(any(target_os = \"android\", target_os = \"ios\")))".dependencies]
tauri-plugin-global-shortcut = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_global_shortcut::Builder::default().build())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-global-shortcut": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { register } from '@tauri-apps/plugin-global-shortcut';
  await register('CommandOrControl+Shift+C', () => {
    console.log('Shortcut triggered');
  });
  ```
 * Rust 
  ```rust
  use tauri_plugin_global_shortcut::GlobalShortcutExt;


  tauri::Builder::default()
      .plugin(
          tauri_plugin_global_shortcut::Builder::new().with_handler(|app, shortcut| {
              println!("Shortcut triggered: {:?}", shortcut);
          })
          .build(),
      )
      .setup(|app| {
          // register a global shortcut
          // on macOS, the Cmd key is used
          // on Windows and Linux, the Ctrl key is used
          app.global_shortcut().register("CmdOrCtrl+Y")?;
          Ok(())
      })
  ```
 ### Migrate to HTTP Plugin The Rust `tauri::api::http` JavaScript `@tauri-apps/api/http` APIs have been removed. Use the `@tauri-apps/plugin-http` plugin instead: 1. Add to cargo dependencies: Cargo.toml 
```toml
[dependencies]
tauri-plugin-http = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_http::init())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-http": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { fetch } from '@tauri-apps/plugin-http';
  const response = await fetch(
    'https://raw.githubusercontent.com/tauri-apps/tauri/dev/package.json'
  );
  ```
 * Rust 
  ```rust
  use tauri_plugin_http::reqwest;


  tauri::Builder::default()
      .plugin(tauri_plugin_http::init())
      .setup(|app| {
          let response_data = tauri::async_runtime::block_on(async {
              let response = reqwest::get(
                  "https://raw.githubusercontent.com/tauri-apps/tauri/dev/package.json",
              )
              .await
              .unwrap();
              response.text().await
          })?;
          Ok(())
      })
  ```
 The HTTP plugin re-exports [reqwest](https://docs.rs/reqwest/latest/reqwest/) so you can check out their documentation for more information. ### Migrate to Notification Plugin The Rust `tauri::api::notification` JavaScript `@tauri-apps/api/notification` APIs have been removed. Use the `@tauri-apps/plugin-notification` plugin instead: 1. Add to cargo dependencies: Cargo.toml 
```toml
[dependencies]
tauri-plugin-notification = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_notification::init())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-notification": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { sendNotification } from '@tauri-apps/plugin-notification';
  sendNotification('Tauri is awesome!');
  ```
 * Rust 
  ```rust
  use tauri_plugin_notification::NotificationExt;
  use tauri::plugin::PermissionState;


  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_notification::init())
          .setup(|app| {
              if app.notification().permission_state()? == PermissionState::Unknown {
                  app.notification().request_permission()?;
              }
              if app.notification().permission_state()? == PermissionState::Granted {
                  app.notification()
                      .builder()
                      .body("Tauri is awesome!")
                      .show()?;
              }
              Ok(())
          })
  }
  ```
 ### Migrate to Menu Module The Rust `Menu` APIs were moved to the `tauri::menu` module and refactored to use the [muda crate](https://github.com/tauri-apps/muda). #### Use `tauri::menu::MenuBuilder` Use `tauri::menu::MenuBuilder` instead of `tauri::Menu`. Note that its constructor takes a Manager instance (one of `App`, `AppHandle` or `WebviewWindow`) as an argument: 
```rust
use tauri::menu::MenuBuilder;


tauri::Builder::default()
    .setup(|app| {
        let menu = MenuBuilder::new(app)
            .copy()
            .paste()
            .separator()
            .undo()
            .redo()
            .text("open-url", "Open URL")
            .check("toggle", "Toggle")
            .icon("show-app", "Show App", app.default_window_icon().cloned().unwrap())
            .build()?;
        app.set_menu(menu);
        Ok(())
    })
```
 #### Use `tauri::menu::PredefinedMenuItem` Use `tauri::menu::PredefinedMenuItem` instead of `tauri::MenuItem`: 
```rust
use tauri::menu::{MenuBuilder, PredefinedMenuItem};


tauri::Builder::default()
    .setup(|app| {
        let menu = MenuBuilder::new(app).item(&PredefinedMenuItem::copy(app)?).build()?;
        Ok(())
    })
```
 #### Use `tauri::menu::MenuItemBuilder` Use `tauri::menu::MenuItemBuilder` instead of `tauri::CustomMenuItem`: 
```rust
use tauri::menu::MenuItemBuilder;


tauri::Builder::default()
    .setup(|app| {
        let toggle = MenuItemBuilder::new("Toggle").accelerator("Ctrl+Shift+T").build(app)?;
        Ok(())
    })
```
 #### Use `tauri::menu::SubmenuBuilder` Use `tauri::menu::SubmenuBuilder` instead of `tauri::Submenu`: 
```rust
use tauri::menu::{MenuBuilder, SubmenuBuilder};


tauri::Builder::default()
    .setup(|app| {
        let submenu = SubmenuBuilder::new(app, "Sub")
            .text("Tauri")
            .separator()
            .check("Is Awesome")
            .build()?;
        let menu = MenuBuilder::new(app).item(&submenu).build()?;
        Ok(())
    })
```
 `tauri::Builder::menu` now takes a closure because the menu needs a Manager instance to be built. See [the documentation](https://docs.rs/tauri/2.0.0/tauri/struct.Builder.html#method.menu) for more information. #### Menu Events The Rust `tauri::Builder::on_menu_event` API was removed. Use `tauri::App::on_menu_event` or `tauri::AppHandle::on_menu_event` instead: 
```rust
use tauri::menu::{CheckMenuItemBuilder, MenuBuilder, MenuItemBuilder};


tauri::Builder::default()
    .setup(|app| {
        let toggle = MenuItemBuilder::with_id("toggle", "Toggle").build(app)?;
        let check = CheckMenuItemBuilder::new("Mark").build(app)?;
        let menu = MenuBuilder::new(app).items(&[&toggle, &check]).build()?;


        app.set_menu(menu)?;


        app.on_menu_event(move |app, event| {
            if event.id() == check.id() {
                println!("`check` triggered, do something! is checked? {}", check.is_checked().unwrap());
            } else if event.id() == "toggle" {
                println!("toggle triggered!");
            }
        });
        Ok(())
    })
```
 Note that there are two ways to check which menu item was selected: move the item to the event handler closure and compare IDs, or define a custom ID for the item through the `with_id` constructor and use that ID string to compare. ### Migrate to OS Plugin The Rust `tauri::api::os` JavaScript `@tauri-apps/api/os` APIs have been removed. Use the `@tauri-apps/plugin-os` plugin instead: 1. Add to cargo dependencies: Cargo.toml 
```toml
[dependencies]
tauri-plugin-os = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_os::init())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-os": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { arch } from '@tauri-apps/plugin-os';
  const architecture = await arch();
  ```
 * Rust 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_os::init())
          .setup(|app| {
              let os_arch = tauri_plugin_os::arch();
              Ok(())
          })
  }
  ```
 ### Migrate to Process Plugin The Rust `tauri::api::process` JavaScript `@tauri-apps/api/process` APIs have been removed. Use the `@tauri-apps/plugin-process` plugin instead: 1. Add to cargo dependencies: Cargo.toml 
```toml
[dependencies]
tauri-plugin-process = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_process::init())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-process": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { exit, relaunch } from '@tauri-apps/plugin-process';
  await exit(0);
  await relaunch();
  ```
 * Rust 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_process::init())
          .setup(|app| {
              // exit the app with a status code
              app.handle().exit(1);
              // restart the app
              app.handle().restart();
              Ok(())
          })
  }
  ```
 ### Migrate to Shell Plugin The Rust `tauri::api::shell` JavaScript `@tauri-apps/api/shell` APIs have been removed. Use the `@tauri-apps/plugin-shell` plugin instead: 1. Add to cargo dependencies: Cargo.toml 
```toml
[dependencies]
tauri-plugin-shell = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_shell::init())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-shell": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { Command, open } from '@tauri-apps/plugin-shell';
  const output = await Command.create('echo', 'message').execute();


  await open('https://github.com/tauri-apps/tauri');
  ```
 * Rust * Open an URL 
  ```rust
  use tauri_plugin_shell::ShellExt;


  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_shell::init())
          .setup(|app| {
              app.shell().open("https://github.com/tauri-apps/tauri", None)?;
              Ok(())
          })
  }
  ```
 * Spawn a child process and retrieve the status code 
  ```rust
  use tauri_plugin_shell::ShellExt;


  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_shell::init())
          .setup(|app| {
              let status = tauri::async_runtime::block_on(async move { app.shell().command("which").args(["ls"]).status().await.unwrap() });
              println!("`which` finished with status: {:?}", status.code());
              Ok(())
          })
  }
  ```
 * Spawn a child process and capture its output 
  ```rust
  use tauri_plugin_shell::ShellExt;


  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_shell::init())
          .setup(|app| {
              let output = tauri::async_runtime::block_on(async move { app.shell().command("echo").args(["TAURI"]).output().await.unwrap() });
              assert!(output.status.success());
              assert_eq!(String::from_utf8(output.stdout).unwrap(), "TAURI");
              Ok(())
          })
  }
  ```
 * Spawn a child process and read its events asynchronously: 
  ```rust
  use tauri_plugin_shell::{ShellExt, process::CommandEvent};


  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_shell::init())
          .setup(|app| {
              let handle = app.handle().clone();
              tauri::async_runtime::spawn(async move {
                  let (mut rx, mut child) = handle.shell().command("cargo")
                      .args(["tauri", "dev"])
                      .spawn()
                      .expect("Failed to spawn cargo");


                  let mut i = 0;
                  while let Some(event) = rx.recv().await {
                      if let CommandEvent::Stdout(line) = event {
                          println!("got: {}", String::from_utf8(line).unwrap());
                         i += 1;
                         if i == 4 {
                             child.write("message from Rust\n".as_bytes()).unwrap();
                             i = 0;
                         }
                     }
                  }
              });
              Ok(())
          })
  }
  ```
 ### Migrate to Tray Icon Module The Rust `SystemTray` APIs were renamed to `TrayIcon` for consistency. The new APIs can be found in the Rust `tray` module. #### Use `tauri::tray::TrayIconBuilder` Use `tauri::tray::TrayIconBuilder` instead of `tauri::SystemTray`: 
```rust
let tray = tauri::tray::TrayIconBuilder::with_id("my-tray").build(app)?;
```
 See [TrayIconBuilder](https://docs.rs/tauri/2.0.0/tauri/tray/struct.TrayIconBuilder.html) for more information. #### Migrate to Menu Use `tauri::menu::Menu` instead of `tauri::SystemTrayMenu`, `tauri::menu::Submenu` instead of `tauri::SystemTraySubmenu` and `tauri::menu::PredefinedMenuItem` instead of `tauri::SystemTrayMenuItem`. #### Tray Events `tauri::SystemTray::on_event` have been split into `tauri::tray::TrayIconBuilder::on_menu_event` and `tauri::tray::TrayIconBuilder::on_tray_icon_event`: 
```rust
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};


tauri::Builder::default()
    .setup(|app| {
        let toggle = MenuItemBuilder::with_id("toggle", "Toggle").build(app)?;
        let menu = MenuBuilder::new(app).items(&[&toggle]).build()?;
        let tray = TrayIconBuilder::new()
            .menu(&menu)
            .on_menu_event(move |app, event| match event.id().as_ref() {
                "toggle" => {
                    println!("toggle clicked");
                }
                _ => (),
            })
            .on_tray_icon_event(|tray, event| {
                if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                } = event
                {
                    let app = tray.app_handle();
                    if let Some(webview_window) = app.get_webview_window("main") {
                       let _ = webview_window.unminimize();
                       let _ = webview_window.show();
                       let _ = webview_window.set_focus();
                    }
                }
            })
            .build(app)?;


        Ok(())
    })
```
 ### Migrate to Updater Plugin Change of default behavior The built-in dialog with an automatic update check was removed, use the Rust and JS APIs to check for and install updates instead. Failing to do so will prevent your users from getting further updates! The Rust `tauri::updater` and JavaScript `@tauri-apps/api-updater` APIs have been removed. To set a custom updater target with the `@tauri-apps/plugin-updater`: 1. Add to cargo dependencies: 
```toml
[dependencies]
tauri-plugin-updater = "2"
```
 2. Use in JavaScript or Rust project: * JavaScript 
  ```rust
  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_updater::Builder::new().build())
  }
  ```
 package.json 
  ```json
  {
    "dependencies": {
      "@tauri-apps/plugin-updater": "^2.0.0"
    }
  }
  ```
 
  ```javascript
  import { check } from '@tauri-apps/plugin-updater';
  import { relaunch } from '@tauri-apps/plugin-process';


  const update = await check();
  if (update?.available) {
    console.log(`Update to ${update.version} available! Date: ${update.date}`);
    console.log(`Release notes: ${update.body}`);
    await update.downloadAndInstall();
    // requires the `process` plugin
    await relaunch();
  }
  ```
 * Rust To check for updates: 
  ```rust
  use tauri_plugin_updater::UpdaterExt;


  fn main() {
      tauri::Builder::default()
          .plugin(tauri_plugin_updater::Builder::new().build())
          .setup(|app| {
              let handle = app.handle();
              tauri::async_runtime::spawn(async move {
                  let response = handle.updater().check().await;
              });
              Ok(())
          })
  }
  ```
 To set a custom updater target: 
  ```rust
  fn main() {
      let mut updater = tauri_plugin_updater::Builder::new();
      #[cfg(target_os = "macos")]
      {
          updater = updater.target("darwin-universal");
      }
      tauri::Builder::default()
          .plugin(updater.build())
  }
  ```
 ### Migrate Path to Tauri Manager The Rust `tauri::api::path` module functions and `tauri::PathResolver` have been moved to `tauri::Manager::path`: 
```rust
use tauri::{path::BaseDirectory, Manager};


tauri::Builder::default()
    .setup(|app| {
        let home_dir_path = app.path().home_dir().expect("failed to get home dir");


        let path = app.path().resolve("path/to/something", BaseDirectory::Config)?;


        Ok(())
  })
```
 ### Migrate to new Window API On the Rust side, `Window` was renamed to `WebviewWindow`, its builder `WindowBuilder` is now named `WebviewWindowBuilder` and `WindowUrl` is now named `WebviewUrl`. Additionally, the `Manager::get_window` function was renamed to `get_webview_window` and the window’s `parent_window` API was renamed to `parent_raw` to support a high level window parent API. On the JavaScript side, the `WebviewWindow` class is now exported in the `@tauri-apps/api/webviewWindow` path. The `onMenuClicked` function was removed, you can intercept menu events when creating a menu in JavaScript instead. ### Migrate Embedded Additional Files (Resources) On the JavaScript side, make sure you [Migrate to File System Plugin](#migrate-to-file-system-plugin). Additionally, note the changes made to the v1 allowlist in [Migrate Permissions](#migrate-permissions). On the Rust side, make sure you [Migrate Path to Tauri Manager](#migrate-path-to-tauri-manager). ### Migrate Embedded External Binaries (Sidecar) In Tauri v1, the external binaries and their arguments were defined in the allowlist. In v2, use the new permissions system. Read [Migrate Permissions](#migrate-permissions) for more information. On the JavaScript side, make sure you [Migrate to Shell Plugin](#migrate-to-shell-plugin). On the Rust side, `tauri::api::process` API has been removed. Use `tauri_plugin_shell::ShellExt` and `tauri_plugin_shell::process::CommandEvent` APIs instead. Read the [Embedding External Binaries](/develop/sidecar/#running-it-from-rust) guide to see how. The “process-command-api” features flag has been removed in v2. So running the external binaries does not require this feature to be defined in the Tauri config anymore. ### Migrate Permissions The v1 allowlist have been rewritten to a completely new system for permissions that works for individual plugins and is much more configurable for multiwindow and remote URL support. This new system works like an access control list (ACL) where you can allow or deny commands, allocate permissions to a specific set of windows and domains, and define access scopes. To enable permissions for your app, you must create capability files inside the `src-tauri/capabilities` folder, and Tauri will automatically configure everything else for you. The `migrate` CLI command automatically parses your v1 allowlist and generates the associated capability file. To learn more about permissions and capabilities, see [the security documentation](/security/).

# Upgrade from Tauri 2.0 Beta

This guide walks you through upgrading your Tauri 2.0 beta application to Tauri 2.0 release candidate. ## Automated Migration The Tauri v2 CLI includes a `migrate` command that automates most of the process and helps you finish the migration: * npm 
  ```sh
  npm install @tauri-apps/cli@latest
  npm run tauri migrate
  ```
 * yarn 
  ```sh
  yarn upgrade @tauri-apps/cli@latest
  yarn tauri migrate
  ```
 * pnpm 
  ```sh
  pnpm update @tauri-apps/cli@latest
  pnpm tauri migrate
  ```
 * cargo 
  ```sh
  cargo install tauri-cli --version "^2.0.0" --locked
  cargo tauri migrate
  ```
 Learn more about the `migrate` command in the [Command Line Interface reference](/reference/cli/#migrate) ## Breaking Changes We have had several breaking changes going from beta to release candidate. These can be either auto-migrated (see above) or manually performed. ### Tauri Core Plugins We changed how Tauri built-in plugins are addressed in the capabilities [PR #10390](https://github.com/tauri-apps/tauri/pull/10390). To migrate from the latest beta version you need to prepend all core permission identifiers in your capabilities with `core:` or switch to the `core:default` permission and remove old core plugin identifiers. 
```json
...
"permissions": [
    "path:default",
    "event:default",
    "window:default",
    "app:default",
    "image:default",
    "resources:default",
    "menu:default",
    "tray:default",
]
...
```
 
```json
...
"permissions": [
    "core:path:default",
    "core:event:default",
    "core:window:default",
    "core:app:default",
    "core:image:default",
    "core:resources:default",
    "core:menu:default",
    "core:tray:default",
]
...
```
 We also added a new special `core:default` permission set which will contain all default permissions of all core plugins, so you can simplify the permissions boilerplate in your capabilities config. 
```json
...
"permissions": [
    "core:default"
]
...
```
 ### Built-In Development Server We introduced changes to the network exposure of the built-in development server [PR #10437](https://github.com/tauri-apps/tauri/pull/10437) and [PR #10456](https://github.com/tauri-apps/tauri/pull/10456). The built-in mobile development server no longer exposes network wide and tunnels traffic from the local machine directly to the device. Currently this improvement does not automatically apply when running on iOS devices (either directly or from Xcode). In this case we default to using the public network address for the development server, but there’s a way around it which involves opening Xcode to automatically start a connection between your macOS machine and your connected iOS device, then running `tauri ios dev --force-ip-prompt` to select the iOS device’s TUN address (ends with **::2**). Your development server configuration needs to adapt to this change if running on a physical iOS device is intended. Previously we recommended checking if the `TAURI_ENV_PLATFORM` environment variable matches either `android` or `ios`, but since we can now connect to localhost unless using an iOS device, you should instead check the `TAURI_DEV_HOST` environment variable. Here’s an example of a Vite configuration migration: * 2.0.0-beta: 
```js
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { internalIpV4Sync } from 'internal-ip';


const mobile = !!/android|ios/.exec(process.env.TAURI_ENV_PLATFORM);


export default defineConfig({
  plugins: [svelte()],
  clearScreen: false,
  server: {
    host: mobile ? '0.0.0.0' : false,
    port: 1420,
    strictPort: true,
    hmr: mobile
      ? {
          protocol: 'ws',
          host: internalIpV4Sync(),
          port: 1421,
        }
      : undefined,
  },
});
```
 * 2.0.0: 
```js
import { defineConfig } from 'vite';
import Unocss from 'unocss/vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';


const host = process.env.TAURI_DEV_HOST;


export default defineConfig({
  plugins: [svelte()],
  clearScreen: false,
  server: {
    host: host || false,
    port: 1420,
    strictPort: true,
    hmr: host
      ? {
          protocol: 'ws',
          host: host,
          port: 1430,
        }
      : undefined,
  },
});
```
 Note The `internal-ip` NPM package is no longer required, you can directly use the TAURI_DEV_HOST value instead.

# Prerequisites

In order to get started building your project with Tauri you’ll first need to install a few dependencies: 1. [System Dependencies](#system-dependencies) 2. [Rust](#rust) 3. [Configure for Mobile Targets](#configure-for-mobile-targets) (only required if developing for mobile) ## System Dependencies Follow the link to get started for your respective operating system: * [Linux](#linux) (see below for specific distributions) * [macOS Catalina (10.15) and later](#macos) * [Windows 7 and later](#windows) ### Linux Tauri requires various system dependencies for development on Linux. These may be different depending on your distribution but we’ve included some popular distributions below to help you get setup. * Debian 
  ```sh
  sudo apt update
  sudo apt install libwebkit2gtk-4.1-dev \
    build-essential \
    curl \
    wget \
    file \
    libxdo-dev \
    libssl-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
  ```
 * Arch 
  ```sh
  sudo pacman -Syu
  sudo pacman -S --needed \
    webkit2gtk-4.1 \
    base-devel \
    curl \
    wget \
    file \
    openssl \
    appmenu-gtk-module \
    libappindicator-gtk3 \
    librsvg \
    xdotool
  ```
 * Fedora 
  ```sh
  sudo dnf check-update
  sudo dnf install webkit2gtk4.1-devel \
    openssl-devel \
    curl \
    wget \
    file \
    libappindicator-gtk3-devel \
    librsvg2-devel \
    libxdo-devel
  sudo dnf group install "c-development"
  ```
 * Gentoo 
  ```sh
  sudo emerge --ask \
    net-libs/webkit-gtk:4.1 \
    dev-libs/libayatana-appindicator \
    net-misc/curl \
    net-misc/wget \
    sys-apps/file
  ```
 * OSTree 
  ```sh
  sudo rpm-ostree install webkit2gtk4.1-devel \
    openssl-devel \
    curl \
    wget \
    file \
    libappindicator-gtk3-devel \
    librsvg2-devel \
    libxdo-devel \
    gcc \
    gcc-c++ \
    make
  sudo systemctl reboot
  ```
 * openSUSE 
  ```sh
  sudo zypper up
  sudo zypper in webkit2gtk3-devel \
    libopenssl-devel \
    curl \
    wget \
    file \
    libappindicator3-1 \
    librsvg-devel
  sudo zypper in -t pattern devel_basis
  ```
 * Alpine 
  ```sh
  sudo apk add \
    build-base \
    webkit2gtk-4.1-dev \
    curl \
    wget \
    file \
    openssl \
    libayatana-appindicator-dev \
    librsvg
  ```
 > Note: Alpine Linux containers don’t include any fonts by default. To ensure text renders correctly in your Tauri app, install at least one font package (for example, `font-dejavu `). > Note: Alpine targets the musl C library, so Rust builds link a number of system libraries statically. If `cargo`/`pnpm tauri build` fails with linker errors for symbols from libraries that `pkg-config` reports as present, install the matching `*-static` packages alongside the `-dev` ones above: > > ```sh > sudo apk add --no-cache \ > openssl-libs-static \ > cairo-static \ > harfbuzz-static \ > glib-static \ > wayland-static \ > zlib-static > ``` > > Not every dependency Tauri pulls in is packaged as `*-static` on Alpine; in those cases you may need to build the missing static library from source. * NixOS Note Instructions for Nix/NixOS can be found in the [NixOS Wiki](https://wiki.nixos.org/wiki/Tauri). If your distribution isn’t included above then you may want to check [Awesome Tauri on GitHub](https://github.com/tauri-apps/awesome-tauri#guides) to see if a guide has been created. Next: [Install Rust](#rust) ### macOS Tauri uses [Xcode](https://developer.apple.com/xcode/resources/) and various macOS and iOS development dependencies. Download and install Xcode from one of the following places: * [Mac App Store](https://apps.apple.com/gb/app/xcode/id497799835?mt=12) * [Apple Developer website](https://developer.apple.com/xcode/resources/). Be sure to launch Xcode after installing so that it can finish setting up. Next: [Install Rust](#rust) ### Windows Tauri uses the Microsoft C++ Build Tools for development as well as Microsoft Edge WebView2. These are both required for development on Windows. Follow the steps below to install the required dependencies. #### Microsoft C++ Build Tools 1. Download the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) installer and open it to begin installation. 2. During installation check the “Desktop development with C++” option. ![Visual Studio C++ Build Tools installer screenshot](/_astro/visual-studio-build-tools-installer.BWhlyd8N_J78Jx.webp) Next: [Install WebView2](#webview2). #### WebView2 Tauri uses Microsoft Edge WebView2 to render content on Windows. Install WebView2 by visiting the [WebView2 Runtime download section](https://developer.microsoft.com/en-us/microsoft-edge/webview2/#download-section). Download the “Evergreen Bootstrapper” and install it. Next: [Check VBSCRIPT](#vbscript-for-msi-installers) #### VBSCRIPT (for MSI installers) MSI package building only This is only required if you plan to build MSI installer packages (`"targets": "msi"` or `"targets": "all"` in `tauri.conf.json`). Building MSI packages on Windows requires the VBSCRIPT optional feature to be enabled. This feature is enabled by default on most Windows installations, but may have been disabled on some systems. If you encounter errors like `failed to run light.exe` when building MSI packages, you may need to enable the VBSCRIPT feature: 1. Open **Settings** → **Apps** → **Optional features** → **More Windows features** 2. Locate **VBSCRIPT** in the list and ensure it’s checked 3. Click **Next** and restart your computer if prompted **Note:** VBSCRIPT is currently enabled by default on most Windows installations, but is [being deprecated](https://techcommunity.microsoft.com/blog/windows-itpro-blog/vbscript-deprecation-timelines-and-next-steps/4148301) and may be disabled in future Windows versions. Next: [Install Rust](#rust) ## Rust Tauri is built with [Rust](https://www.rust-lang.org) and requires it for development. Install Rust using one of following methods. You can view more installation methods at <https://www.rust-lang.org/tools/install>. * Linux and macOS Install via [`rustup`](https://github.com/rust-lang/rustup) using the following command: 
  ```sh
  curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh
  ```
 * Windows Visit <https://www.rust-lang.org/tools/install> to install `rustup`. Alternatively, you can use `winget` to install rustup using the following command in PowerShell: 
  ```powershell
  winget install --id Rustlang.Rustup
  ```
 MSVC toolchain as default For full support for Tauri and tools like [`trunk`](https://trunk-rs.github.io/trunk/) make sure the MSVC Rust toolchain is the selected `default host triple` in the installer dialog. Depending on your system it should be either `x86_64-pc-windows-msvc`, `i686-pc-windows-msvc`, or `aarch64-pc-windows-msvc`. If you already have Rust installed, you can make sure the correct toolchain is installed by running this command: 
  ```powershell
  rustup default stable-msvc
  ```
 **Be sure to restart your Terminal (and in some cases your system) for the changes to take effect.** Next: [Configure for Mobile Targets](#configure-for-mobile-targets) if you’d like to build for Android and iOS, or, if you’d like to use a JavaScript framework, [install Node](#nodejs). Otherwise [Create a Project](/start/create-project/). ## Node.js JavaScript ecosystem Only if you intend to use a JavaScript frontend framework 1. Go to the [Node.js website](https://nodejs.org), download the Long Term Support (LTS) version and install it. 2. Check if Node was successfully installed by running: 
```sh
node -v
# v20.10.0
npm -v
# 10.2.3
```
 It’s important to restart your Terminal to ensure it recognizes the new installation. In some cases, you might need to restart your computer. While npm is the default package manager for Node.js, you can also use others like pnpm or yarn. To enable these, run `corepack enable` in your Terminal. This step is optional and only needed if you prefer using a package manager other than npm. Next: [Configure for Mobile Targets](#configure-for-mobile-targets) or [Create a project](/start/create-project/). ## Configure for Mobile Targets If you’d like to target your app for Android or iOS then there are a few additional dependencies that you need to install: * [Android](#android) * [iOS](#ios) ### Android 1. Download and install [Android Studio from the Android Developers website](https://developer.android.com/studio) 2. Set the `JAVA_HOME` environment variable: * Linux 
  ```sh
  export JAVA_HOME=/opt/android-studio/jbr
  ```
 * macOS 
  ```sh
  export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
  ```
 * Windows 
  ```ps
  [System.Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\Program Files\Android\Android Studio\jbr", "User")
  ```
 3. Use the SDK Manager in Android Studio to install the following: * Android SDK Platform * Android SDK Platform-Tools * NDK (Side by side) * Android SDK Build-Tools * Android SDK Command-line Tools Selecting “Show Package Details” in the SDK Manager enables the installation of older package versions. Only install older versions if necessary, as they may introduce compatibility issues or security risks. 4. Set `ANDROID_HOME` and `NDK_HOME` environment variables. * Linux 
  ```sh
  export ANDROID_HOME="$HOME/Android/Sdk"
  export NDK_HOME="$ANDROID_HOME/ndk/$(ls -1 $ANDROID_HOME/ndk)"
  ```
 * macOS 
  ```sh
  export ANDROID_HOME="$HOME/Library/Android/sdk"
  export NDK_HOME="$ANDROID_HOME/ndk/$(ls -1 $ANDROID_HOME/ndk)"
  ```
 * Windows 
  ```ps
  [System.Environment]::SetEnvironmentVariable("ANDROID_HOME", "$env:LocalAppData\Android\Sdk", "User")
  $VERSION = Get-ChildItem -Name "$env:LocalAppData\Android\Sdk\ndk" | Select-Object -Last 1
  [System.Environment]::SetEnvironmentVariable("NDK_HOME", "$env:LocalAppData\Android\Sdk\ndk\$VERSION", "User")
  ```
 5. Add the Android targets with `rustup`: 
```sh
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
```
 Next: [Setup for iOS](#ios) or [Create a project](/start/create-project/). ### iOS macOS Only iOS development requires Xcode and is only available on macOS. Be sure that you’ve installed Xcode and not Xcode Command Line Tools in the [macOS system dependencies section](#macos). 1. Add the iOS targets with `rustup` in Terminal: 
```sh
rustup target add aarch64-apple-ios x86_64-apple-ios aarch64-apple-ios-sim
```
 2. Install [Homebrew](https://brew.sh): 
```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
 3. Install [Cocoapods](https://cocoapods.org) using Homebrew: 
```sh
brew install cocoapods
```
 Next: [Create a project](/start/create-project/). ## Troubleshooting If you run into any issues during installation be sure to check the [Troubleshooting Guide](/develop/debug/) or reach out on the [Tauri Discord](https://discord.com/invite/tauri). Next Steps Now that you’ve installed all of the prerequisites you’re ready to [create your first Tauri project](/start/create-project/)!

# Project Structure

A Tauri project is usually made of 2 parts, a Rust project and a JavaScript project (optional), and typically the setup looks something like this: 
```plaintext
.
├── package.json
├── index.html
├── src/
│   ├── main.js
├── src-tauri/
│   ├── Cargo.toml
│   ├── Cargo.lock
│   ├── build.rs
│   ├── tauri.conf.json
│   ├── src/
│   │   ├── main.rs
│   │   └── lib.rs
│   ├── icons/
│   │   ├── icon.png
│   │   ├── icon.icns
│   │   └── icon.ico
│   └── capabilities/
│       └── default.json
```
 In this case, the JavaScript project is at the top level, and the Rust project is inside `src-tauri/`, the Rust project is a normal [Cargo project](https://doc.rust-lang.org/cargo/guide/project-layout.html) with some extra files: * `tauri.conf.json` is the main configuration file for Tauri, it contains everything from the application identifier to dev server url, this file is also a marker for the [Tauri CLI](/reference/cli/) to find the Rust project, to learn more about it, see [Tauri Config](/develop/configuration-files/#tauri-config) * `capabilities/` directory is the default folder Tauri reads [capability files](/security/capabilities/) from (in short, you need to allow commands here to use them in your JavaScript code), to learn more about it, see [Security](/security/) * `icons/` directory is the default output directory of the [`tauri icon`](/reference/cli/#icon) command, it’s usually referenced in `tauri.conf.json > bundle > icon` and used for the app’s icons * `build.rs` contains `tauri_build::build()` which is used for tauri’s build system * `src/lib.rs` contains the Rust code and the mobile entry point (the function marked with `#[cfg_attr(mobile, tauri::mobile_entry_point)]`), the reason we don’t write directly in `main.rs` is because we compile your app to a library in mobile builds and load them through the platform frameworks * `src/main.rs` is the main entry point for the desktop, and we run `app_lib::run()` in `main` to use the same entry point as mobile, so to keep it simple, don’t modify this file, modify `lib.rs` instead. Note that `app_lib` corresponds to `[lib.name]` in Cargo.toml. Tauri works similar to a static web host, and the way it builds is that you would compile your JavaScript project to static files first, and then compile the Rust project that will bundle those static files in, so the JavaScript project setup is basically the same as if you were to build a static website, to learn more, see [Frontend Configuration](/start/frontend/) If you want to work with Rust code only, simply remove everything else and use the `src-tauri/` folder as your top level project or as a member of your Rust workspace ## Next Steps * [Add and Configure a Frontend Framework](/start/frontend/) * [Tauri Command Line Interface (CLI) Reference](/reference/cli/) * [Learn how to develop your Tauri app](/develop/) * [Discover additional features to extend Tauri](/plugin/)

# About Tauri

> Various information about Tauri from governance, philosophy, and trademark guidelines

[Tauri Philosophy](/about/philosophy/)Learn more about the approach behind Tauri [Governance](/about/governance/)Understand how the Tauri governance structure is setup [Trademark](/about/trademark/)Guidelines for using the Tauri trademark

# The Tauri Book

Progress Update We’re actively working on authoring and writing The Tauri Book. We’ve encountered delays due to the immense growth of Tauri but have recently re-prioritized this project. While we don’t yet have details on the timelines of a release, you can keep an eye on this page for updates. We’d like to apologize for this being delayed beyond the originally communicated publish date. If you’ve donated through GitHub Sponsors or Open Collective and would like to request a refund you may do so via Open Collective: [Contact Tauri on Open Collective](https://opencollective.com/tauri/contact). ### Overview The Tauri Book will guide you through the history of Tauri and the design decisions we’ve made. It will also talk in depth about why privacy, security and sustainability are important and fundamental discussions you can apply to any modern software project. Topics included are: * The method and reasoning behind the design of Tauri * The options you have when building with Tauri * That you don’t have to choose between shipping fast and being sustainable and responsible * Why we chose the Rust language as a binding and application layer for Tauri * Why a binary review is important ### History In 2020, the manufacture of native-apps has become easier and more accessible than ever before. All the same, beginners and seasoned developers alike are confronted with tough choices in a rapidly changing landscape of security and privacy. This is especially true in the semi-trusted environment of user devices. Tauri takes the guesswork out of the equation, as it was designed from the ground up to embrace new paradigms of secure development and creative flexibility that leverage the language features of Rust and lets you build an app using any frontend framework you like. Find out how you can design, build, audit and deploy tiny, fast, robust, and secure native applications for the major desktop and mobile platforms, all from the exact same codebase and in record time - without even needing to know the Rust programming language. Authors and Tauri co-founders Daniel and Lucas take you on a journey from theory to execution, during which you will learn why Tauri was built and how it works under the hood. Together with guest insights that specialize in Open Source, DevOps, Security and Enterprise Architecture, this book also presents discourse-formatted philosophical discussions and open-source sustainability viewpoints from which your next-gen apps will profit - and your users will benefit.

# Tauri Governance

One of the main goals of the organizational structure of Tauri is to guarantee we stay true to our open source values and do so sustainably while respecting the health and well-being of contributors. [The Tauri Programme within the Commons Conservancy](https://dracc.commonsconservancy.org/0035/) was established to commit to those values, and facilitate an open, transparent and efficient governance process throughout the future development of the Tauri and its auxiliary materials. ## Tauri Working Group The Tauri Working Group is the collective framework created to enable this governance process. It’s composed of the following components: * Working Group Members * Tauri Board & Board Directors * Domains & Domain Leads * Teams ![Tauri governance diagram](/_astro/diagram.ByZzOWqU_M4e8i.svg) ### Working Group Members All of the individuals that make up the Tauri Working Group. ### Tauri Board & Board Directors The Tauri Board is the central decision making body for the Tauri Programme and is responsible for the overall health and stability of the Tauri Programme. The Board votes on major decisions within the Programme and issues raised by the Working Group. An individual Board Director may be a technical contributor, be a stakeholder in Tauri’s future, share experience from the industry, or have a passion for regulatory and legal aspects within Open Source. ### Domains & Domain Leads Domains are organizational units that represent an area of interest within Tauri. Domain Leads are trusted contributors within the Tauri community with expertise in the Domain they are leading. They are responsible for setting direction, overseeing and supporting the activities within that Domain. The current Domains and Domain leads are outlined in the [Governance and Guidance repo on GitHub](https://github.com/tauri-apps/governance-and-guidance). ### Teams Teams are small groups of contributors that support or maintain specific areas of the Tauri Programme. They are a means for Tauri to execute its longer-term tasks and goals, especially when ad-hoc contributions cannot achieve the same results. ## Get Involved If you’re interested in becoming a Tauri Board Director or a Domain Lead, elections for those positions are run throughout the year. For Domain Leads those take place in both the spring and fall and for Board Directors in the summer. Instructions for how to apply are posted to the [Tauri Blog](/blog/) leading up to the respective election. ## Additional Resources * [Governance and Guidance Repository](https://github.com/tauri-apps/governance-and-guidance): More detailed information about Tauri’s Governance and the current Domains and Domain Leads * [Social Contract](https://github.com/tauri-apps/governance-and-guidance/blob/main/SOCIAL_CONTRACT.md): The social contract informs our decision making and organization * [Code of Conduct](https://github.com/tauri-apps/governance-and-guidance/blob/main/CODE_OF_CONDUCT.md) * [Tauri Programme Statutes](https://dracc.commonsconservancy.org/0035/)

# Tauri Philosophy

Tauri is a toolkit that helps developers make applications for the major desktop platforms - using virtually any frontend framework in existence. The core is built with Rust, and the CLI leverages Node.js making Tauri a genuinely polyglot approach to creating and maintaining great apps. [YouTube video player](https://www.youtube-nocookie.com/embed/UxTJeEbZX-0?si=mwQUzXb6mmCg7aom) ## Security First In today’s world, every honest threat model assumes that the user’s device has already been compromised. This puts app developers in a complicated situation because if the device is already at risk, how can the software be trusted? Defense in depth is the approach we’ve taken. We want you to be able to take every precaution possible to minimize the surface area you present to attackers. Tauri lets you choose which API endpoints to ship, whether or not you want a localhost server built into your app, and it even randomizes functional handles at runtime. These and other techniques form a secure baseline that empowers you and your users. Slowing down attackers by making static attacks crushingly difficult and isolating systems from one another is the name of the game. And if you are coming from the Electron ecosystem - rest assured - by default Tauri only ships binaries, not ASAR files. By choosing to build Tauri with security as a guiding force, we give you every opportunity to take a proactive security posture. ## Polyglots, not Silos Most contemporary frameworks use a single language paradigm and are therefore trapped in a bubble of knowledge and idiom. This can work well for certain niche applications, but it also fosters a kind of tribalism. This can be seen in the way that the React, Angular, and Vue development communities huddle on their stacks, ultimately breeding very little cross-pollination. This same situation can be seen in the Rust vs. Node vs. C++ battlefields, where hardliners take their stances and refuse to collaborate across communities. Today, Tauri uses Rust for the backend - but in the not too distant future, other backends like Go, Nim, Python, Csharp, etc. will be possible. This is because we are maintaining the official Rust bindings to the [webview](https://github.com/webview) organization and plan to let you switch out the backend for your needs. Since our API can be implemented in any language with C interop, full compliance is only a PR away. ## Honest Open Source None of this would make any sense without a community. Today software communities are amazing places where people help each other and make awesome things - open source is a very big part of that. Open source means different things to different people, but most will agree that it serves to support freedom. When software doesn’t respect your rights, then it can seem unfair and potentially compromise your freedoms by operating in unethical ways. This is why we are proud that FLOSS advocates can build applications with Tauri that are “certifiably” open source and can be included in FSF endorsed GNU/Linux distributions. ## The Future Tauri’s future depends on your involvement and contributions. Try it out, file issues, join a working group or make a donation - every contribution is important. Please, at any rate, do get in touch!!!

# Trademark Guidelines

This trademark policy was prepared to help you understand how to use the TAURI trademarks, service marks and logos owned by the Tauri Programme within the Commons Conservancy. While our software is available under a free and open source software license, that copyright license does not include a license to use our trademark, and this Policy is intended to explain how to use our marks consistent with background law and community expectation. **This Policy covers:** * Our word trademarks and service marks: TAURI, TAO, WRY * Our logos: The TAURI, TAO, WRY logos (and all visual derivatives) This policy encompasses all trademarks and service marks, whether they are registered or not. ## General Guidelines Whenever you use one of our marks, you must always do so in a way that does not mislead anyone about what they are getting and from whom. For example, you cannot say you are distributing TAURI software when you’re distributing a modified version of it (aka a Fork), because recipients may not understand the differences between your modified versions and our own. You also cannot use our logo on your website in a way that suggests that your website is an official website or that we endorse your website. You can, though, say you like TAURI software, that you participate in the TAURI community, that you are providing an unmodified version of the TAURI software. You may not use or register our marks, or variations of them as part of your own trademark, service mark, domain name, company name, trade name, product name or service name. Trademark law does not allow your use of names or trademarks that are too similar to ours. You therefore may not use an obvious variation of any of our marks or any phonetic equivalent, foreign language equivalent, takeoff, or abbreviation for a similar or compatible product or service. We would consider the following too similar to one of our Marks: * TAURIMAGE * Tauri Wallet App ## Acceptable Uses ### Applications TAURI is a framework for making applications for computing devices. You may claim that your application uses TAURI, but care should be taken to avoid giving the impression that your application is approved by The Tauri Programme within the Commons Conservancy, or is an official application. Care must be taken, not to ship your application with the default ICON. ### Plugins & Templates You may publish the code for plugins and templates using the appropriate naming conventions, but please mention that these works are not officially approved. Only such codebases that are managed by the organization within the GitHub organization `tauri-apps` are considered official. ## Core Modifications (Forks) If you distribute a modified version of our software (TAURI CORE), you must remove all of our logos and naming from it. You must retain our original license in SPDX format. You may use our word marks, but not our logos, to truthfully describe the origin of the software that you are providing. For example, if the code you are distributing is a modification of our software, you may say, “This software is derived from the source code for TAURI software.” ### Statements About Compatibility You may use the word marks, but not the logos, to truthfully describe the relationship between your software and ours. Any other use may imply that we have certified or approved your software. If you wish to use our logos, please contact us to discuss license terms. ### Naming Compatible Products If you wish to describe your product with reference to the TAURI software, here are the conditions under which you may do so. You may call your software XYZ (where XYZ is your product name) for TAURI only if: * All versions of the TAURI software you deliver with your product are the exact binaries provided by us, or manufactured by the core software and tooling we provide. * Your product is fully compatible with the APIs for the TAURI software. * You use the following legend in marketing materials or product descriptions: “TAURI is a trademark of The Tauri Programme within the Commons Conservancy. <https://tauri.app/> ” ### User Groups You can use the Word Marks as part of your user group name provided that: * The main focus of the group is our software * The group does not make a profit * Any charge to attend meetings are to cover the cost of the venue, food and drink only You are not authorized to conduct a conference using our marks. ### No Domain Names You must not register any domain that includes our word marks or any variant or combination of them. ### Other For Profit Usage of the TAURI Marks If you are making a video, tutorial series, book, or other educational material, for which you are receiving payment through subscriptions, sales, advertising or the like, then you must acquire explicit licensing permission from The Tauri Programme within the Commons Conservancy. ## How to Display Our Marks When you have the right to use our mark, here is how to display it. ### Trademark Marking and Legends The first or most prominent mention of a mark on a webpage, document, or documentation should be accompanied by a symbol indicating whether the mark is a registered trademark (“®”) or an unregistered trademark (“™”). If you don’t know which applies, contact us. (TAURI itself is a registered trademark.) Place the following notice at the foot of the page where you have used the mark: TAURI is trademark of \[The Tauri Programme within the Commons Conservancy].” ### Use of Trademarks in Text Always use trademarks in their exact form with the correct spelling, neither abbreviated, hyphenated, or combined with any other word or words. * Unacceptable: TAUREE * Acceptable: TAURI Don’t pluralize a trademark. * Unacceptable: I have seventeen TAURIs running on my computer. * Acceptable: I am running seventeen TAURI applications on my computer and have ram to spare. Always use a trademark as an adjective modifying a noun. * Unacceptable: This is a TAURI. * Acceptable: This is a TAURI software application. ### Use of Logos You may not change any logo except to scale it. This means you may not add decorative elements, change the colors, change the proportions, distort it, add elements, or combine it with other logos. We have a high-contrast version of the logo, which you can download below in the assets section. ## Assets * Here you may download the entire [Brand Guidelines](/assets/brand_guidelines.pdf) - (PDF, 74.3 MB) * Here you may download SVG and PNG formats of the LOGO and Wordmark in the [Logopack](/assets/logopack.zip) - (ZIP, 203 KB) *** The Tauri Programme within the Commons Conservancy retains all rights to the modification of these trademark guidelines at any time. If you have a question or enquiry, please send an email to `trademark@tauri.app`. These guidelines are based on the Model Trademark Guidelines, available at <http://www.modeltrademarkguidelines.org>, used under a Creative Commons Attribution 3.0 Unported license: <https://creativecommons.org/licenses/by/3.0/deed.en_EU>. Version 1.0 dated 20th, August 2022

# Core Concepts

> Topics that you should get more intimately familiar with if you want to get the most out of the framework

Tauri has a variety of topics that are considered to be core concepts, things any developer should be aware of when developing their applications. Here’s a variety of topics that you should get more intimately familiar with if you want to get the most out of the framework. [Tauri Architecture](/concept/architecture/)Architecture and ecosystem. [Inter-Process Communication (IPC)](/concept/inter-process-communication/)The inner workings on the IPC. [Security](/security/)How Tauri enforces security practices. [Process Model](/concept/process-model/)Which processes Tauri manages and why. [App Size](/concept/size/)How to make your app as small as possible.

# Tauri Architecture

## Introduction Tauri is a polyglot and generic toolkit that is very composable and allows engineers to make a wide variety of applications. It is used for building applications for desktop computers using a combination of Rust tools and HTML rendered in a Webview. Apps built with Tauri can ship with any number of pieces of an optional JS API and Rust API so that webviews can control the system via message passing. Developers can extend the default API with their own functionality and bridge the Webview and Rust-based backend easily. Tauri apps can have [tray-type interfaces](/learn/system-tray/). They can be [updated](/plugin/updater/) and are managed by the user’s operating system as expected. They are very small because they use the OS’s webview. They do not ship a runtime since the final binary is compiled from Rust. This makes the [reversing of Tauri apps not a trivial task](/security/). ### What Tauri is Not Tauri is not a lightweight kernel wrapper. Instead, it directly uses [WRY](#wry) and [TAO](#tao) to do the heavy lifting in making system calls to the OS. Tauri is not a VM or virtualized environment. Instead, it is an application toolkit that allows making Webview OS applications. ## Core Ecosystem Simplified representation of the Tauri architecture. ### tauri [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri) This is the major crate that holds everything together. It brings the runtimes, macros, utilities and API into one final product. It reads the [`tauri.conf.json`](/reference/config/) file at compile time to bring in features and undertake the actual configuration of the app (and even the `Cargo.toml` file in the project’s folder). It handles script injection (for polyfills / prototype revision) at runtime, hosts the API for systems interaction, and even manages the updating process. ### tauri-runtime [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-runtime) The glue layer between Tauri itself and lower-level webview libraries. ### tauri-macros [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-macros) Creates macros for the context, handler, and commands by leveraging the [`tauri-codegen`](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-codegen) crate. ### tauri-utils [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-utils) Common code that is reused in many places and offers useful utilities like parsing configuration files, detecting platform triples, injecting the CSP, and managing assets. ### tauri-build [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-build) Applies the macros at build-time to rig some special features needed by `cargo`. ### tauri-codegen [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-codegen) Embeds, hashes, and compresses assets, including icons for the app as well as the system tray. Parses [`tauri.conf.json`](/reference/config/) at compile time and generates the Config struct. ### tauri-runtime-wry [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-runtime-wry) This crate opens up direct systems-level interactions specifically for WRY, such as printing, monitor detection, and other windowing-related tasks. ## Tauri Tooling ### API (JavaScript / TypeScript) [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/packages/api) A typescript library that creates `cjs` and `esm` JavaScript endpoints for you to import into your frontend framework so that the Webview can call and listen to backend activity. Also ships in pure typescript, because for some frameworks this is more optimal. It uses the message passing of webviews to their hosts. ### Bundler (Rust / Shell) [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-bundler) A library that builds a Tauri app for the platform it detects or is told. Currently supports macOS, Windows and Linux - but in the near future will support mobile platforms as well. May be used outside of Tauri projects. ### cli.rs (Rust) [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-cli) This Rust executable provides the full interface to all of the required activities for which the CLI is required. It runs on macOS, Windows, and Linux. ### cli.js (JavaScript) [View on GitHub](https://github.com/tauri-apps/tauri/tree/dev/packages/cli) Wrapper around [`cli.rs`](https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-cli) using [`napi-rs`](https://github.com/napi-rs/napi-rs) to produce npm packages for each platform. ### create-tauri-app (JavaScript) [View on GitHub](https://github.com/tauri-apps/create-tauri-app) A toolkit that will enable engineering teams to rapidly scaffold out a new `tauri-apps` project using the frontend framework of their choice (as long as it has been configured). ## Upstream Crates The Tauri-Apps organization maintains two “upstream” crates from Tauri, namely TAO for creating and managing application windows, and WRY for interfacing with the Webview that lives within the window. ### TAO [View on GitHub](https://github.com/tauri-apps/tao) Cross-platform application window creation library in Rust that supports all major platforms like Windows, macOS, Linux, iOS and Android. Written in Rust, it is a fork of [winit](https://github.com/rust-windowing/winit) that we have extended for our own needs - like menu bar and system tray. ### WRY [View on GitHub](https://github.com/tauri-apps/wry) WRY is a cross-platform WebView rendering library in Rust that supports all major desktop platforms like Windows, macOS, and Linux. Tauri uses WRY as the abstract layer responsible to determine which webview is used (and how interactions are made). ## Additional Tooling ### tauri-action [View on GitHub](https://github.com/tauri-apps/tauri-action) GitHub workflow that builds Tauri binaries for all platforms. Even allows creating a (very basic) Tauri app even if Tauri is not set up. ### tauri-vscode [View on GitHub](https://github.com/tauri-apps/tauri-vscode) This project enhances the Visual Studio Code interface with several nice-to-have features. ## Plugins [Tauri Plugin Guide](/develop/plugins/) Generally speaking, plugins are authored by third parties (even though there may be official, supported plugins). A plugin generally does 3 things: 1. Enables Rust code to do “something”. 2. Provides interface glue to make it easy to integrate into an app. 3. Provides a JavaScript API for interfacing with the Rust code. Here are some examples of Tauri Plugins: * [tauri-plugin-fs](https://github.com/tauri-apps/tauri-plugin-fs) * [tauri-plugin-sql](https://github.com/tauri-apps/tauri-plugin-sql) * [tauri-plugin-stronghold](https://github.com/tauri-apps/tauri-plugin-stronghold) ## License Tauri itself is licensed under MIT or Apache-2.0. If you repackage it and modify any source code, it is your responsibility to verify that you are complying with all upstream licenses. Tauri is provided AS-IS with no explicit claim for suitability for any purpose. Here you may peruse our [Software Bill of Materials](https://app.fossa.com/projects/git%2Bgithub.com%2Ftauri-apps%2Ftauri).

# Inter-Process Communication

Inter-Process Communication (IPC) allows isolated processes to communicate securely and is key to building more complex applications. Learn more about the specific IPC patterns in the following guides: [Brownfield](/concept/inter-process-communication/brownfield/) [Isolation](/concept/inter-process-communication/isolation/) Tauri uses a particular style of Inter-Process Communication called [Asynchronous Message Passing](https://en.wikipedia.org/wiki/Message_passing#Asynchronous_message_passing), where processes exchange *requests* and *responses* serialized using some simple data representation. Message Passing should sound familiar to anyone with web development experience, as this paradigm is used for client-server communication on the internet. Message passing is a safer technique than shared memory or direct function access because the recipient is free to reject or discard requests as it sees fit. For example, if the Tauri Core process determines a request to be malicious, it simply discards the requests and never executes the corresponding function. In the following, we explain Tauri’s two IPC primitives - `Events` and `Commands` - in more detail. ## Events Events are fire-and-forget, one-way IPC messages that are best suited to communicate lifecycle events and state changes. Unlike [Commands](#commands), Events can be emitted by both the Frontend *and* the Tauri Core. Events sent between the Core and the Webview. Under the hood, events still utilize Commands, and the access to the events API is controlled by the [Event permissions](/reference/acl/core-permissions/#event). ## Commands Tauri also provides a [foreign function interface](https://en.wikipedia.org/wiki/Foreign_function_interface)-like abstraction on top of IPC messages[1](#user-content-fn-1). The primary API, `invoke`, is similar to the browser’s `fetch` API and allows the Frontend to invoke Rust functions, pass arguments, and receive data. Because this mechanism uses a [JSON-RPC](https://www.jsonrpc.org) like protocol under the hood to serialize requests and responses, all arguments and return data must be serializable to JSON. IPC messages involved in a command invocation. ## Footnotes 1. Because Commands still use message passing under the hood, they do not share the same security pitfalls as real FFI interfaces do. [↩](#user-content-fnref-1)

# Brownfield Pattern

***This is the default pattern.*** This is the simplest and most straightforward pattern to use Tauri with, because it tries to be as compatible as possible with existing frontend projects. In short, it tries to require nothing additional to what an existing web frontend might use inside a browser. Not ***everything*** that works in existing browser applications will work out-of-the-box. If you are unfamiliar with Brownfield software development in general, the [Brownfield Wikipedia article](https://en.wikipedia.org/wiki/Brownfield_\(software_development\)) provides a nice summary. For Tauri, the existing software is current browser support and behavior, instead of legacy systems. ## Configuration Because the Brownfield pattern is the default pattern, it doesn’t require a configuration option to be set. To explicitly set it, you can use the `app > security > pattern` object in the `tauri.conf.json` configuration file. 
```json
{
  "app": {
    "security": {
      "pattern": {
        "use": "brownfield"
      }
    }
  }
}
```
 ***There are no additional configuration options for the brownfield pattern.***

# Isolation Pattern

The Isolation pattern is a way to intercept and modify Tauri API messages sent by the frontend before they get to Tauri Core, all with JavaScript. The secure JavaScript code that is injected by the Isolation pattern is referred to as the Isolation application. ## Why The Isolation pattern’s purpose is to provide a mechanism for developers to help protect their application from unwanted or malicious frontend calls to Tauri Core. The need for the Isolation pattern rose out of threats coming from untrusted content running on the frontend, a common case for applications with many dependencies. See [Security: Threat Models](/security/lifecycle/) for a list of many sources of threats that an application may see. The largest threat model described above that the Isolation pattern was designed in mind was Development Threats. Not only do many frontend build-time tools consist of many dozen (or hundreds) of often deeply-nested dependencies, but a complex application may also have a large amount of (also often deeply-nested) dependencies that are bundled into the final output. ## When Tauri highly recommends using the isolation pattern whenever it can be used. Because the Isolation application intercepts ***all*** messages from the frontend, it can *always* be used. Tauri also strongly suggests locking down your application whenever you use external Tauri APIs. As the developer, you can utilize the secure Isolation application to try and verify IPC inputs, to make sure they are within some expected parameters. For example, you may want to check that a call to read or write a file is not trying to access a path outside your application’s expected locations. Another example is making sure that a Tauri API HTTP fetch call is only setting the Origin header to what your application expects it to be. That said, it intercepts ***all*** messages from the frontend, so it will even work with always-on APIs such as [Events](/reference/javascript/api/namespaceevent/). Since some events may cause your own rust code to perform actions, the same sort of validation techniques can be used with them. ## How The Isolation pattern is all about injecting a secure application in between your frontend and Tauri Core to intercept and modify incoming IPC messages. It does this by using the sandboxing feature of `<iframe>`s to run the JavaScript securely alongside the main frontend application. Tauri enforces the Isolation pattern while loading the page, forcing all IPC calls to Tauri Core to instead be routed through the sandboxed Isolation application first. Once the message is ready to be passed to Tauri Core, it is encrypted using the browser’s [SubtleCrypto](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto) implementation and passed back to the main frontend application. Once there, it is directly passed to Tauri Core, where it is then decrypted and read like normal. To ensure that someone cannot manually read the keys for a specific version of your application and use that to modify the messages after being encrypted, new keys are generated each time your application is run. ### Approximate Steps of an IPC Message To make it easier to follow, here’s an ordered list with the approximate steps an IPC message will go through when being sent to Tauri Core with the Isolation pattern: 1. Tauri’s IPC handler receives a message 2. IPC handler -> Isolation application 3. `[sandbox]` Isolation application hook runs and potentially modifies the message 4. `[sandbox]` Message is encrypted with AES-GCM using a runtime-generated key 5. `[encrypted]` Isolation application -> IPC handler 6. `[encrypted]` IPC handler -> Tauri Core *Note: Arrows (->) indicate message passing.* ### Performance Implications Because encryption of the message does occur, there are additional overhead costs compared to the [Brownfield pattern](/concept/inter-process-communication/brownfield/), even if the secure Isolation application doesn’t do anything. Aside from performance-sensitive applications (who likely have a carefully-maintained and small set of dependencies, to keep the performance adequate), most applications should not notice the runtime costs of encrypting/decrypting the IPC messages, as they are relatively small and AES-GCM is relatively fast. If you are unfamiliar with AES-GCM, all that is relevant in this context is that it’s the only authenticated mode algorithm included in [SubtleCrypto](https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto) and that you probably already use it every day under the hood with [TLS](https://en.wikipedia.org/wiki/Transport_Layer_Security). There is also a cryptographically secure key generated once each time the Tauri application is started. It is not generally noticeable if the system already has enough entropy to immediately return enough random numbers, which is extremely common for desktop environments. If running in a headless environment to perform some [integration testing with WebDriver](/develop/tests/webdriver/) then you may want to install some sort of entropy-generating service such as `haveged` if your operating system does not have one included. Linux 5.6 (March 2020) now includes entropy generation using speculative execution. ### Limitations There are a few limitations in the Isolation pattern that arose out of platform inconsistencies. The most significant limitation is due to external files not loading correctly inside sandboxed `<iframes>` on Windows. Because of this, we have implemented a simple script inlining step during build time that takes the content of scripts relative to the Isolation application and injects them inline. This means that typical bundling or simple including of files like `<script src="index.js"></script>` still works properly, but newer mechanisms such as ES Modules will *not* successfully load. ## Recommendations Because the point of the Isolation application is to protect against Development Threats, we highly recommend keeping your Isolation application as simple as possible. Not only should you strive to keep dependencies of your isolation application minimal, but you should also consider keeping its required build steps minimal. This would allow you to not need to worry about supply chain attacks against your Isolation application on top of your frontend application. ## Creating the Isolation Application In this example, we will make a small hello-world style Isolation application and hook it up to an imaginary existing Tauri application. It will do no verification of the messages passing through it, only print the contents to the WebView console. For the purposes of this example, let’s imagine we are in the same directory as `tauri.conf.json`. The existing Tauri application has its `frontendDist` set to `../dist`. `../dist-isolation/index.html`: 
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Isolation Secure Script</title>
  </head>
  <body>
    <script src="index.js"></script>
  </body>
</html>
```
 `../dist-isolation/index.js`: 
```javascript
window.__TAURI_ISOLATION_HOOK__ = (payload) => {
  // let's not verify or modify anything, just print the content from the hook
  console.log('hook', payload);
  return payload;
};
```
 Now, all we need to do is set up our `tauri.conf.json` [configuration](#configuration) to use the Isolation pattern, and have just bootstrapped to the Isolation pattern from the [Brownfield pattern](/concept/inter-process-communication/brownfield/). ## Configuration Let’s assume that our main frontend `frontendDist` is set to `../dist`. We also output our Isolation application to `../dist-isolation`. 
```json
{
  "build": {
    "frontendDist": "../dist"
  },
  "app": {
    "security": {
      "pattern": {
        "use": "isolation",
        "options": {
          "dir": "../dist-isolation"
        }
      }
    }
  }
}
```

# Process Model

Tauri employs a multi-process architecture similar to Electron or many modern web browsers. This guide explores the reasons behind the design choice and why it is key to writing secure applications. ## Why Multiple Processes? In the early days of GUI applications, it was common to use a single process to perform computation, draw the interface and react to user input. As you can probably guess, this meant that a long-running, expensive computation would leave the user interface unresponsive, or worse, a failure in one app component would bring the whole app crashing down. It became clear that a more resilient architecture was needed, and applications began running different components in different processes. This makes much better use of modern multi-core CPUs and creates far safer applications. A crash in one component doesn’t affect the whole system anymore, as components are isolated on different processes. If a process gets into an invalid state, we can easily restart it. We can also limit the blast radius of potential exploits by handing out only the minimum amount of permissions to each process, just enough so they can get their job done. This pattern is known as the [Principle of Least Privilege](https://en.wikipedia.org/wiki/Principle_of_least_privilege), and you see it in the real world all the time. If you have a gardener coming over to trim your hedge, you give them the key to your garden. You would **not** give them the keys to your house; why would they need access to that? The same concept applies to computer programs. The less access we give them, the less harm they can do if they get compromised. ## The Core Process Each Tauri application has a core process, which acts as the application’s entry point and which is the only component with full access to the operating system. The Core’s primary responsibility is to use that access to create and orchestrate application windows, system-tray menus, or notifications. Tauri implements the necessary cross-platform abstractions to make this easy. It also routes all [Inter-Process Communication](/concept/inter-process-communication/) through the Core process, allowing you to intercept, filter, and manipulate IPC messages in one central place. The Core process should also be responsible for managing global state, such as settings or database connections. This allows you to easily synchronize state between windows and protect your business-sensitive data from prying eyes in the Frontend. We chose Rust to implement Tauri because of its concept of [Ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html) guarantees memory safety while retaining excellent performance. Simplified representation of the Tauri process model. A single Core process manages one or more WebView processes. ## The WebView Process The Core process doesn’t render the actual user interface (UI) itself; it spins up WebView processes that leverage WebView libraries provided by the operating system. A WebView is a browser-like environment that executes your HTML, CSS, and JavaScript. This means that most of your techniques and tools used in traditional web development can be used to create Tauri applications. For example, many Tauri examples are written using the [Svelte](https://svelte.dev/) frontend framework and the [Vite](https://vitejs.dev/) bundler. Security best practices apply as well; for example, you must always sanitize user input, never handle secrets in the Frontend, and ideally defer as much business logic as possible to the Core process to keep your attack surface small. Unlike other similar solutions, the WebView libraries are **not** included in your final executable but dynamically linked at runtime[1](#user-content-fn-1). This makes your application *significantly* smaller, but it also means that you need to keep platform differences in mind, just like traditional web development. ## Footnotes 1. Currently, Tauri uses [Microsoft Edge WebView2](https://docs.microsoft.com/en-us/microsoft-edge/webview2/) on Windows, [WKWebView](https://developer.apple.com/documentation/webkit/wkwebview) on macOS and [webkitgtk](https://webkitgtk.org) on Linux. [↩](#user-content-fnref-1)

# App Size

While Tauri by default provides very small binaries it doesn’t hurt to push the limits a bit, so here are some tips and tricks for reaching optimal results. ## Cargo Configuration One of the simplest frontend agnostic size improvements you can do to your project is adding a Cargo profile to it. Dependent on whether you use the stable or nightly Rust toolchain the options available to you differ a bit. It’s recommended you stick to the stable toolchain unless you’re an advanced user. * Stable src-tauri/Cargo.toml 
  ```toml
  [profile.dev]
  incremental = true # Compile your binary in smaller steps.


  [profile.release]
  codegen-units = 1 # Allows LLVM to perform better optimization.
  lto = true # Enables link-time-optimizations.
  opt-level = "s" # Prioritizes small binary size. Use `3` if you prefer speed.
  panic = "abort" # Higher performance by disabling panic handlers.
  strip = true # Ensures debug symbols are removed.
  ```
 * Nightly src-tauri/Cargo.toml 
  ```toml
  [profile.dev]
  incremental = true # Compile your binary in smaller steps.
  rustflags = ["-Zthreads=8"] # Better compile performance.


  [profile.release]
  codegen-units = 1 # Allows LLVM to perform better optimization.
  lto = true # Enables link-time-optimizations.
  opt-level = "s" # Prioritizes small binary size. Use `3` if you prefer speed.
  panic = "abort" # Higher performance by disabling panic handlers.
  strip = true # Ensures debug symbols are removed.
  trim-paths = "all" # Removes potentially privileged information from your binaries.
  rustflags = ["-Cdebuginfo=0", "-Zthreads=8"] # Better compile performance.
  ```
 ### References Note This is not a complete reference over all available options, merely the ones that we’d like to draw extra attention to. * [incremental:](https://doc.rust-lang.org/cargo/reference/profiles.html#incremental) Compile your binary in smaller steps. * [codegen-units:](https://doc.rust-lang.org/cargo/reference/profiles.html#codegen-units) Speeds up compile times at the cost of compile time optimizations. * [lto:](https://doc.rust-lang.org/cargo/reference/profiles.html#lto) Enables link time optimizations. * [opt-level:](https://doc.rust-lang.org/cargo/reference/profiles.html#opt-level) Determines the focus of the compiler. Use `3` to optimize performance, `z` to optimize for size, and `s` for something in-between. * [panic:](https://doc.rust-lang.org/cargo/reference/profiles.html#panic) Reduce size by removing panic unwinding. * [strip:](https://doc.rust-lang.org/cargo/reference/profiles.html#strip) Strip either symbols or debuginfo from a binary. * [rpath:](https://doc.rust-lang.org/cargo/reference/profiles.html#rpath) Assists in finding the dynamic libraries the binary requires by hard coding information into the binary. * [trim-paths:](https://rust-lang.github.io/rfcs/3127-trim-paths.html) Removes potentially privileged information from binaries. * [rustflags:](https://doc.rust-lang.org/nightly/cargo/reference/unstable.html#profile-rustflags-option) Sets Rust compiler flags on a profile by profile basis. * `-Cdebuginfo=0`: Whether debuginfo symbols should be included in the build. * `-Zthreads=8`: Increases the number of threads used during compilation. ## Remove Unused Commands In Pull Request [`feat: add a new option to remove unused commands`](https://github.com/tauri-apps/tauri/pull/12890), we added in a new option in the tauri config file tauri.conf.json 
```json
{
  "build": {
    "removeUnusedCommands": true
  }
}
```
 to remove commands that’re never allowed in your capability files (ACL), so you don’t have to pay for what you don’t use Note This feature requires `tauri@2.4`, `tauri-build@2.1`, `tauri-plugin@2.1` and `tauri-cli@2.4` Note This won’t be accounting for dynamically added ACLs at runtime so make sure to check it when using this

# Develop

> Topics pertaining to the development of Tauri applications, including how to use the Tauri API, communicating between the frontend and backend, configuration, state management, debugging and more

Now that you have [everything set up](/start/), you are ready to run your application using Tauri. If you are using a UI framework or JavaScript bundler, you likely have access to a development server that will speed up your development process, so if you haven’t configured your app’s dev URL and script that starts it, you can do so via the [devUrl](/reference/config/#devurl) and [beforeDevCommand](/reference/config/#beforedevcommand) config values: tauri.conf.json 
```json
{
  "build": {
    "devUrl": "http://localhost:3000",
    "beforeDevCommand": "npm run dev"
  }
}
```
 Note Every framework has its own development tooling. It is outside of the scope of this document to cover them all or stay up to date. Please refer to your framework’s documentation to learn more and determine the correct values to be configured. Otherwise, if you are not using a UI framework or module bundler, you can point Tauri to your frontend source code and the Tauri CLI will start a development server for you: tauri.conf.json 
```json
{
  "build": {
    "frontendDist": "./src"
  }
}
```
 Note that in this example, the `src` folder must include an `index.html` file along with any other assets loaded by your frontend. Plain/Vanilla Dev Server Security The built-in Tauri development server does not support mutual authentication or encryption. You should never use it for development on untrusted networks. See the [development server security considerations](/security/lifecycle/#development-server) for a more detailed explanation. ## Developing Your Desktop Application To develop your application for desktop, run the `tauri dev` command. * npm 
  ```sh
  npm run tauri dev
  ```
 * yarn 
  ```sh
  yarn tauri dev
  ```
 * pnpm 
  ```sh
  pnpm tauri dev
  ```
 * deno 
  ```sh
  deno task tauri dev
  ```
 * bun 
  ```sh
  bun tauri dev
  ```
 * cargo 
  ```sh
  cargo tauri dev
  ```
 The first time you run this command, the Rust package manager may need **several minutes** to download and build all the required packages. Since they are cached, subsequent builds are much faster, as only your code needs rebuilding. Once Rust has finished building, the webview opens, displaying your web app. You can make changes to your web app, and if your tooling supports it, the webview should update automatically, just like a browser. ### Opening the Web Inspector You can open the Web Inspector to debug your application by performing a right-click on the webview and clicking “Inspect” or using the `Ctrl + Shift + I` shortcut on Windows and Linux or `Cmd + Option + I` shortcut on macOS. ## Developing Your Mobile Application Developing for mobile is similar to how desktop development works, but you must run `tauri android dev` or `tauri ios dev` instead: * npm 
  ```sh
  npm run tauri [android|ios] dev
  ```
 * yarn 
  ```sh
  yarn tauri [android|ios] dev
  ```
 * pnpm 
  ```sh
  pnpm tauri [android|ios] dev
  ```
 * deno 
  ```sh
  deno task tauri [android|ios] dev
  ```
 * bun 
  ```sh
  bun tauri [android|ios] dev
  ```
 * cargo 
  ```sh
  cargo tauri [android|ios] dev
  ```
 The first time you run this command, the Rust package manager may need **several minutes** to download and build all the required packages. Since they are cached, subsequent builds are much faster, as only your code needs rebuilding. ### Development Server The development server on mobile works similarly to the desktop one, but if you are trying to run on a physical iOS device, you must configure it to listen to a particular address provided by the Tauri CLI, defined in the `TAURI_DEV_HOST` environment variable. This address is either a public network address (which is the default behavior) or the actual iOS device TUN address — which is more secure, but currently needs Xcode to connect to the device. To use the iOS device’s address you must open Xcode before running the dev command and ensure your device is connected via network in the Window > Devices and Simulators menu. Then you must run `tauri ios dev --force-ip-prompt` to select the iOS device address (an IPv6 address ending with **::2**). To make your development server listen on the correct host to be accessible by the iOS device, you must tweak its configuration to use the `TAURI_DEV_HOST` value if it has been provided. Here is an example configuration for Vite: 
```js
import { defineConfig } from 'vite';


const host = process.env.TAURI_DEV_HOST;


// https://vitejs.dev/config/
export default defineConfig({
  clearScreen: false,
  server: {
    host: host || false,
    port: 1420,
    strictPort: true,
    hmr: host
      ? {
          protocol: 'ws',
          host,
          port: 1421,
        }
      : undefined,
  },
});
```
 Check your framework’s setup guide for more information. Note Projects created with [create-tauri-app](https://github.com/tauri-apps/create-tauri-app) configure your development server for mobile dev out of the box. ### Device Selection By default, the mobile dev command tries to run your application on a connected device, and falls back to prompting you to select a simulator to use. To define the run target upfront, you can provide the device or simulator name as an argument: * npm 
  ```sh
  npm run tauri ios dev 'iPhone 15'
  ```
 * yarn 
  ```sh
  yarn tauri ios dev 'iPhone 15'
  ```
 * pnpm 
  ```sh
  pnpm tauri ios dev 'iPhone 15'
  ```
 * deno 
  ```sh
  deno task tauri ios dev 'iPhone 15'
  ```
 * bun 
  ```sh
  bun tauri ios dev 'iPhone 15'
  ```
 * cargo 
  ```sh
  cargo tauri ios dev 'iPhone 15'
  ```
 ### Using Xcode or Android Studio Alternatively you can choose to use Xcode or Android Studio to develop your application. This can help you troubleshoot some development issues by using the IDE instead of the command line tools. To open the mobile IDE instead of running on a connected device or simulator, use the `--open` flag: * npm 
  ```sh
  npm run tauri [android|ios] dev --open
  ```
 * yarn 
  ```sh
  yarn tauri [android|ios] dev --open
  ```
 * pnpm 
  ```sh
  pnpm tauri [android|ios] dev --open
  ```
 * deno 
  ```sh
  deno task tauri [android|ios] dev --open
  ```
 * bun 
  ```sh
  bun tauri [android|ios] dev --open
  ```
 * cargo 
  ```sh
  cargo tauri [android|ios] dev --open
  ```
 Note If you intend to run the application on a physical iOS device, you must also provide the `--host` argument and your development server must use the `process.env.TAURI_DEV_HOST` value as host. See your framework’s setup guide for more information. * npm 
  ```sh
  npm run tauri [android|ios] dev --open --host
  ```
 * yarn 
  ```sh
  yarn tauri [android|ios] dev --open --host
  ```
 * pnpm 
  ```sh
  pnpm tauri [android|ios] dev --open --host
  ```
 * deno 
  ```sh
  deno task tauri [android|ios] dev --open --host
  ```
 * bun 
  ```sh
  bun tauri [android|ios] dev --open --host
  ```
 * cargo 
  ```sh
  cargo tauri [android|ios] dev --open --host
  ```
 Caution To use Xcode or Android Studio, the Tauri CLI process **must** be running and **cannot** be killed. It is recommended to use the `tauri [android|ios] dev --open` command and keep the process alive until you close the IDE. ### Opening the Web Inspector * iOS Safari must be used to access the Web Inspector for your iOS application. Open Safari on your Mac, choose **Safari > Settings** in the menu bar, click **Advanced**, then select **Show features for web developers**. If you are running on a physical device, you must enable **Web Inspector** in **Settings > Safari > Advanced**. After following all steps you should see a **Develop** menu in Safari, where you will find the connected devices and applications to inspect. Select your device or simulator and click on **localhost** to open the Safari Developer Tools window. * Android The inspector is enabled by default for Android emulators, but you must enable it for physical devices. Connect your Android device to the computer, open the **Settings** app on the Android device, select **About**, scroll to Build Number, and tap it 7 times. This will enable Developer Mode for your Android device and the **Developer Options** settings. To enable application debugging on your device, you must enter the **Developer Options** settings, toggle on the developer options switch and enable **USB Debugging**. Note Each Android distribution has its own way to enable the Developer Mode. Please check your manufacturer’s documentation for more information. The Web Inspector for Android is powered by Google Chrome’s DevTools and can be accessed by navigating to `chrome://inspect` in the Chrome browser on your computer. Your device or emulator should appear in the remote devices list if your Android application is running, and you can open the developer tools by clicking **inspect** on the entry matching your device. ### Troubleshooting 1. Error running build script on Xcode Tauri hooks into the iOS Xcode project by creating a build phase that executes the Tauri CLI to compile the Rust source as a library that is loaded at runtime. The build phase is executed on the Xcode process context, so it might not be able to use shell modifications such as PATH additions, so be careful when using tools such as Node.js version managers which may not be compatible. 2. Network permission prompt on first iOS app execution When you first execute `tauri ios dev`, you might see iOS prompting you for permission to find and connect to devices on your local network. This permission is required because, to access your development server from an iOS device, it must be exposed on the local network. To run your app on your device, you must click Allow and restart your application. ## Reacting to Source Code Changes Similarly to how your webview reflects changes in real time, `tauri dev` watches your `src-tauri` folder and its dependent crates in the workspace for changes, so your application is automatically rebuilt and restarted whenever you modify them. You can disable this behavior by using the `--no-watch` flag on the `tauri dev` command. To ignore watching certain files, you can create `.taurignore` files which work like regular `.gitignore` files: .taurignore 
```txt
build/
src/generated/*.rs
deny.toml
```
 `.taurignore` files are usually put in the `src-tauri` directory or [cargo workspace](https://doc.rust-lang.org/cargo/reference/workspaces.html) root folder. Currently, `tauri dev` looks for `.taurignore` files anywhere inside the common ancestor of the watched folders and the Cargo workspace root folder. ## Using the Browser DevTools Tauri’s APIs only work in your app window, so once you start using them you won’t be able to open your frontend in your system’s browser anymore. If you prefer using your browser’s developer tooling, you must configure [tauri-invoke-http](https://github.com/tauri-apps/tauri-invoke-http) to bridge Tauri API calls through a HTTP server. ## Source Control In your project repository, you **SHOULD** commit the `src-tauri/Cargo.lock` along with the `src-tauri/Cargo.toml` to git because Cargo uses the lockfile to provide deterministic builds. As a result, it is recommended that all applications check in their `Cargo.lock`. You **SHOULD NOT** commit the `src-tauri/target` folder or any of its contents.

# Calling the Frontend from Rust

The `@tauri-apps/api` NPM package offers APIs to listen to both global and webview-specific events. * Listening to global events 
  ```ts
  import { listen } from '@tauri-apps/api/event';


  type DownloadStarted = {
    url: string;
    downloadId: number;
    contentLength: number;
  };


  listen<DownloadStarted>('download-started', (event) => {
    console.log(
      `downloading ${event.payload.contentLength} bytes from ${event.payload.url}`
    );
  });
  ```
 * Listening to webview-specific events 
  ```ts
  import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';


  const appWebview = getCurrentWebviewWindow();
  appWebview.listen<string>('logged-in', (event) => {
    localStorage.setItem('session-token', event.payload);
  });
  ```
 The `listen` function keeps the event listener registered for the entire lifetime of the application. To stop listening on an event you can use the `unlisten` function which is returned by the `listen` function: 
```js
import { listen } from '@tauri-apps/api/event';


const unlisten = await listen('download-started', (event) => {});
unlisten();
```
 Note Always use the unlisten function when your execution context goes out of scope such as when a component is unmounted. When the page is reloaded or you navigate to another URL the listeners are unregistered automatically. This does not apply to a Single Page Application (SPA) router though. #### Common Pitfalls ##### Don’t call `unlisten()` before the listener resolves The `listen` function returns a Promise that resolves to the `unlisten` handle. If you call `unlisten` synchronously before the Promise resolves, the handler will be removed immediately and you won’t receive any events: 
```js
// Wrong: unlisten is called before the listener is registered
const unlisten = listen('sync-complete', (event) => {
  console.log('sync finished');
});
unlisten(); // unlisten is a Promise here, not a function -- the listener is not cleaned up


// Correct: await the Promise to get the unlisten handle
const unlisten = await listen('sync-complete', (event) => {
  console.log('sync finished');
});
// Now you can store and call it later, e.g. in a cleanup function
unlisten();
```
 ##### Timing in setup hooks In frameworks like React, Vue, and Svelte, the setup or mount hook runs before the component is fully rendered. If you listen for events during setup, make sure the event handler does not depend on DOM elements that haven’t been rendered yet, or defer the listener registration to an effect/hook that runs after mount. 
```js
// Wrong: DOM ref may not be available yet
function MyComponent() {
  const ref = useRef(null);
  listen('scroll-to', (event) => {
    ref.current.scrollIntoView(); // ref.current may be null during setup
  });
  return <div ref={ref} />;
}


// Correct: use useEffect which runs after the component mounts
function MyComponent() {
  const ref = useRef(null);
  useEffect(() => {
    const unlisten = listen('scroll-to', (event) => {
      ref.current?.scrollIntoView();
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);
  return <div ref={ref} />;
}
```
 ##### Event ordering and async listeners Event listeners are called in the order they are registered, but if a listener is async and the event emitter sends multiple events in rapid succession, the listeners may process events out of order. For ordered, high-throughput data delivery, consider using [Channels](/develop/calling-frontend/#channels) instead of the event system. #### Framework-specific Cleanup Examples When using a frontend framework, you should clean up event listeners when a component is unmounted to avoid memory leaks and duplicate handlers. * React 
  ```tsx
  import { useEffect, useState } from 'react';
  import { listen } from '@tauri-apps/api/event';


  function DownloadTracker() {
    const [progress, setProgress] = useState(0);


    useEffect(() => {
      const unlisten = listen<number>('download-progress', (event) => {
        setProgress(event.payload);
      });


      return () => {
        unlisten.then((fn) => fn());
      };
    }, []);


    return <div>Download progress: {progress}%</div>;
  }
  ```
 * Vue 
  ```vue
  <script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue';
  import { listen } from '@tauri-apps/api/event';


  const progress = ref(0);
  let unlistenPromise;


  onMounted(() => {
    unlistenPromise = listen<number>('download-progress', (event) => {
      progress.value = event.payload;
    });
  });


  onUnmounted(() => {
    unlistenPromise?.then((fn) => fn());
  });
  </script>


  <template>
    <div>Download progress: {{ progress }}%</div>
  </template>
  ```
 * Svelte 
  ```svelte
  <script lang="ts">
  import { listen } from '@tauri-apps/api/event';


  let progress = $state(0);


  $effect(() => {
    const unlistenPromise = listen<number>(
      'download-progress',
      (event) => {
        progress = event.payload;
      }
    );


    return () => {
      unlistenPromise.then((unlisten) => unlisten());
    };
  });
  </script>


  <div>Download progress: {progress}%</div>
  ```
 Additionally Tauri provides a utility function for listening to an event exactly once: 
```js
import { once } from '@tauri-apps/api/event';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';


once('ready', (event) => {});


const appWebview = getCurrentWebviewWindow();
appWebview.once('ready', () => {});
```
 Note Events emitted in the frontend also trigger listeners registered by these APIs. For more information, see the [Calling Rust from the Frontend](/develop/calling-rust/) documentation. #### Listening to Events on Rust Global and webview-specific events are also delivered to listeners registered in Rust. * Listening to global events src-tauri/src/lib.rs 
  ```rust
  use tauri::Listener;


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
    tauri::Builder::default()
      .setup(|app| {
        app.listen("download-started", |event| {
          if let Ok(payload) = serde_json::from_str::<DownloadStarted>(&event.payload()) {
            println!("downloading {}", payload.url);
          }
        });
        Ok(())
      })
      .run(tauri::generate_context!())
      .expect("error while running tauri application");
  }
  ```
 * Listening to webview-specific events src-tauri/src/lib.rs 
  ```rust
  use tauri::{Listener, Manager};


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
    tauri::Builder::default()
      .setup(|app| {
        let webview = app.get_webview_window("main").unwrap();
        webview.listen("logged-in", |event| {
          let session_token = event.data;
          // save token..
        });
        Ok(())
      })
      .run(tauri::generate_context!())
      .expect("error while running tauri application");
  }
  ```
 The `listen` function keeps the event listener registered for the entire lifetime of the application. To stop listening on an event you can use the `unlisten` function: 
```rust
// unlisten outside of the event handler scope:
let event_id = app.listen("download-started", |event| {});
app.unlisten(event_id);


// unlisten when some event criteria is matched
let handle = app.handle().clone();
app.listen("status-changed", |event| {
  if event.data == "ready" {
    handle.unlisten(event.id);
  }
});
```
 Additionally Tauri provides a utility function for listening to an event exactly once: 
```rust
app.once("ready", |event| {
  println!("app is ready");
});
```
 In this case the event listener is immediately unregistered after its first trigger.

# Calling the Frontend from Rust

This document includes guides on how to communicate with your application frontend from your Rust code. To see how to communicate with your Rust code from your frontend, see [Calling Rust from the Frontend](/develop/calling-rust/). The Rust side of your Tauri application can call the frontend by leveraging the Tauri event system, using channels or directly evaluating JavaScript code. ## Event System Tauri ships a simple event system you can use to have bi-directional communication between Rust and your frontend. The event system was designed for situations where small amounts of data need to be streamed or you need to implement a multi consumer multi producer pattern (e.g. push notification system). The event system is not designed for low latency or high throughput situations. See the [channels section](#channels) for the implementation optimized for streaming data. The major differences between a Tauri command and a Tauri event are that events have no strong type support, event payloads are always JSON strings making them not suitable for bigger messages and there is no support of the [capabilities](/security/capabilities/) system to fine grain control event data and channels. The [AppHandle](https://docs.rs/tauri/2.0.0/tauri/struct.AppHandle.html) and [WebviewWindow](https://docs.rs/tauri/2.0.0/tauri/webview/struct.WebviewWindow.html) types implement the event system traits [Listener](https://docs.rs/tauri/2.0.0/tauri/trait.Listener.html) and [Emitter](https://docs.rs/tauri/2.0.0/tauri/trait.Emitter.html). Events are either global (delivered to all listeners) or webview-specific (only delivered to the webview matching a given label). ### Global Events To trigger a global event you can use the [Emitter#emit](https://docs.rs/tauri/2.0.0/tauri/trait.Emitter.html#tymethod.emit) function: src-tauri/src/lib.rs 
```rust
use tauri::{AppHandle, Emitter};


#[tauri::command]
fn download(app: AppHandle, url: String) {
  app.emit("download-started", &url).unwrap();
  for progress in [1, 15, 50, 80, 100] {
    app.emit("download-progress", progress).unwrap();
  }
  app.emit("download-finished", &url).unwrap();
}
```
 Note Global events are delivered to **all** listeners ### Webview Event To trigger an event to a listener registered by a specific webview you can use the [Emitter#emit_to](https://docs.rs/tauri/2.0.0/tauri/trait.Emitter.html#tymethod.emit_to) function: src-tauri/src/lib.rs 
```rust
use tauri::{AppHandle, Emitter};


#[tauri::command]
fn login(app: AppHandle, user: String, password: String) {
  let authenticated = user == "tauri-apps" && password == "tauri";
  let result = if authenticated { "loggedIn" } else { "invalidCredentials" };
  app.emit_to("login", "login-result", result).unwrap();
}
```
 It is also possible to trigger an event to a list of webviews by calling [Emitter#emit_filter](https://docs.rs/tauri/2.0.0/tauri/trait.Emitter.html#tymethod.emit_filter). In the following example we emit an open-file event to the main and file-viewer webviews: src-tauri/src/lib.rs 
```rust
use tauri::{AppHandle, Emitter, EventTarget};


#[tauri::command]
fn open_file(app: AppHandle, path: std::path::PathBuf) {
  app.emit_filter("open-file", path, |target| match target {
    EventTarget::WebviewWindow { label } => label == "main" || label == "file-viewer",
    _ => false,
  }).unwrap();
}
```
 Note Webview-specific events are **not** triggered to regular global event listeners. To listen to **any** event you must use the `listen_any` function instead of `listen`, which defines the listener to act as a catch-all for emitted events. ### Event Payload The event payload can be any [serializable](https://serde.rs/impl-serialize.html) type that also implements [Clone](https://doc.rust-lang.org/std/clone/trait.Clone.html). Let’s enhance the download event example by using an object to emit more information in each event: src-tauri/src/lib.rs 
```rust
use tauri::{AppHandle, Emitter};
use serde::Serialize;


#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct DownloadStarted<'a> {
  url: &'a str,
  download_id: usize,
  content_length: usize,
}


#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct DownloadProgress {
  download_id: usize,
  chunk_length: usize,
}


#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct DownloadFinished {
  download_id: usize,
}


#[tauri::command]
fn download(app: AppHandle, url: String) {
  let content_length = 1000;
  let download_id = 1;


  app.emit("download-started", DownloadStarted {
    url: &url,
    download_id,
    content_length
  }).unwrap();


  for chunk_length in [15, 150, 35, 500, 300] {
    app.emit("download-progress", DownloadProgress {
      download_id,
      chunk_length,
    }).unwrap();
  }


  app.emit("download-finished", DownloadFinished { download_id }).unwrap();
}
```
 ### Listening to Events Tauri provides APIs to listen to events on both the webview and the Rust interfaces. #### Listening to Events on the Frontend The `@tauri-apps/api` NPM package offers APIs to listen to both global and webview-specific events. * Listening to global events 
  ```ts
  import { listen } from '@tauri-apps/api/event';


  type DownloadStarted = {
    url: string;
    downloadId: number;
    contentLength: number;
  };


  listen<DownloadStarted>('download-started', (event) => {
    console.log(
      `downloading ${event.payload.contentLength} bytes from ${event.payload.url}`
    );
  });
  ```
 * Listening to webview-specific events 
  ```ts
  import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';


  const appWebview = getCurrentWebviewWindow();
  appWebview.listen<string>('logged-in', (event) => {
    localStorage.setItem('session-token', event.payload);
  });
  ```
 The `listen` function keeps the event listener registered for the entire lifetime of the application. To stop listening on an event you can use the `unlisten` function which is returned by the `listen` function: 
```js
import { listen } from '@tauri-apps/api/event';


const unlisten = await listen('download-started', (event) => {});
unlisten();
```
 Note Always use the unlisten function when your execution context goes out of scope such as when a component is unmounted. When the page is reloaded or you navigate to another URL the listeners are unregistered automatically. This does not apply to a Single Page Application (SPA) router though. #### Common Pitfalls ##### Don’t call `unlisten()` before the listener resolves The `listen` function returns a Promise that resolves to the `unlisten` handle. If you call `unlisten` synchronously before the Promise resolves, the handler will be removed immediately and you won’t receive any events: 
```js
// Wrong: unlisten is called before the listener is registered
const unlisten = listen('sync-complete', (event) => {
  console.log('sync finished');
});
unlisten(); // unlisten is a Promise here, not a function -- the listener is not cleaned up


// Correct: await the Promise to get the unlisten handle
const unlisten = await listen('sync-complete', (event) => {
  console.log('sync finished');
});
// Now you can store and call it later, e.g. in a cleanup function
unlisten();
```
 ##### Timing in setup hooks In frameworks like React, Vue, and Svelte, the setup or mount hook runs before the component is fully rendered. If you listen for events during setup, make sure the event handler does not depend on DOM elements that haven’t been rendered yet, or defer the listener registration to an effect/hook that runs after mount. 
```js
// Wrong: DOM ref may not be available yet
function MyComponent() {
  const ref = useRef(null);
  listen('scroll-to', (event) => {
    ref.current.scrollIntoView(); // ref.current may be null during setup
  });
  return <div ref={ref} />;
}


// Correct: use useEffect which runs after the component mounts
function MyComponent() {
  const ref = useRef(null);
  useEffect(() => {
    const unlisten = listen('scroll-to', (event) => {
      ref.current?.scrollIntoView();
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);
  return <div ref={ref} />;
}
```
 ##### Event ordering and async listeners Event listeners are called in the order they are registered, but if a listener is async and the event emitter sends multiple events in rapid succession, the listeners may process events out of order. For ordered, high-throughput data delivery, consider using [Channels](/develop/calling-frontend/#channels) instead of the event system. #### Framework-specific Cleanup Examples When using a frontend framework, you should clean up event listeners when a component is unmounted to avoid memory leaks and duplicate handlers. * React 
  ```tsx
  import { useEffect, useState } from 'react';
  import { listen } from '@tauri-apps/api/event';


  function DownloadTracker() {
    const [progress, setProgress] = useState(0);


    useEffect(() => {
      const unlisten = listen<number>('download-progress', (event) => {
        setProgress(event.payload);
      });


      return () => {
        unlisten.then((fn) => fn());
      };
    }, []);


    return <div>Download progress: {progress}%</div>;
  }
  ```
 * Vue 
  ```vue
  <script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue';
  import { listen } from '@tauri-apps/api/event';


  const progress = ref(0);
  let unlistenPromise;


  onMounted(() => {
    unlistenPromise = listen<number>('download-progress', (event) => {
      progress.value = event.payload;
    });
  });


  onUnmounted(() => {
    unlistenPromise?.then((fn) => fn());
  });
  </script>


  <template>
    <div>Download progress: {{ progress }}%</div>
  </template>
  ```
 * Svelte 
  ```svelte
  <script lang="ts">
  import { listen } from '@tauri-apps/api/event';


  let progress = $state(0);


  $effect(() => {
    const unlistenPromise = listen<number>(
      'download-progress',
      (event) => {
        progress = event.payload;
      }
    );


    return () => {
      unlistenPromise.then((unlisten) => unlisten());
    };
  });
  </script>


  <div>Download progress: {progress}%</div>
  ```
 Additionally Tauri provides a utility function for listening to an event exactly once: 
```js
import { once } from '@tauri-apps/api/event';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';


once('ready', (event) => {});


const appWebview = getCurrentWebviewWindow();
appWebview.once('ready', () => {});
```
 Note Events emitted in the frontend also trigger listeners registered by these APIs. For more information, see the [Calling Rust from the Frontend](/develop/calling-rust/) documentation. #### Listening to Events on Rust Global and webview-specific events are also delivered to listeners registered in Rust. * Listening to global events src-tauri/src/lib.rs 
  ```rust
  use tauri::Listener;


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
    tauri::Builder::default()
      .setup(|app| {
        app.listen("download-started", |event| {
          if let Ok(payload) = serde_json::from_str::<DownloadStarted>(&event.payload()) {
            println!("downloading {}", payload.url);
          }
        });
        Ok(())
      })
      .run(tauri::generate_context!())
      .expect("error while running tauri application");
  }
  ```
 * Listening to webview-specific events src-tauri/src/lib.rs 
  ```rust
  use tauri::{Listener, Manager};


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
    tauri::Builder::default()
      .setup(|app| {
        let webview = app.get_webview_window("main").unwrap();
        webview.listen("logged-in", |event| {
          let session_token = event.data;
          // save token..
        });
        Ok(())
      })
      .run(tauri::generate_context!())
      .expect("error while running tauri application");
  }
  ```
 The `listen` function keeps the event listener registered for the entire lifetime of the application. To stop listening on an event you can use the `unlisten` function: 
```rust
// unlisten outside of the event handler scope:
let event_id = app.listen("download-started", |event| {});
app.unlisten(event_id);


// unlisten when some event criteria is matched
let handle = app.handle().clone();
app.listen("status-changed", |event| {
  if event.data == "ready" {
    handle.unlisten(event.id);
  }
});
```
 Additionally Tauri provides a utility function for listening to an event exactly once: 
```rust
app.once("ready", |event| {
  println!("app is ready");
});
```
 In this case the event listener is immediately unregistered after its first trigger. ## Channels The event system is designed to be a simple two way communication that is globally available in your application. Under the hood it directly evaluates JavaScript code so it might not be suitable to sending a large amount of data. Channels are designed to be fast and deliver ordered data. They are used internally for streaming operations such as download progress, child process output and WebSocket messages. Let’s rewrite our download command example to use channels instead of the event system: src-tauri/src/lib.rs 
```rust
use tauri::{AppHandle, ipc::Channel};
use serde::Serialize;


#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase", rename_all_fields = "camelCase", tag = "event", content = "data")]
enum DownloadEvent<'a> {
  Started {
    url: &'a str,
    download_id: usize,
    content_length: usize,
  },
  Progress {
    download_id: usize,
    chunk_length: usize,
  },
  Finished {
    download_id: usize,
  },
}


#[tauri::command]
fn download(app: AppHandle, url: String, on_event: Channel<DownloadEvent>) {
  let content_length = 1000;
  let download_id = 1;


  on_event.send(DownloadEvent::Started {
    url: &url,
    download_id,
    content_length,
  }).unwrap();


  for chunk_length in [15, 150, 35, 500, 300] {
    on_event.send(DownloadEvent::Progress {
      download_id,
      chunk_length,
    }).unwrap();
  }


  on_event.send(DownloadEvent::Finished { download_id }).unwrap();
}
```
 When calling the download command you must create the channel and provide it as an argument: 
```ts
import { invoke, Channel } from '@tauri-apps/api/core';


type DownloadEvent =
  | {
      event: 'started';
      data: {
        url: string;
        downloadId: number;
        contentLength: number;
      };
    }
  | {
      event: 'progress';
      data: {
        downloadId: number;
        chunkLength: number;
      };
    }
  | {
      event: 'finished';
      data: {
        downloadId: number;
      };
    };


const onEvent = new Channel<DownloadEvent>();
onEvent.onmessage = (message) => {
  console.log(`got download event ${message.event}`);
};


await invoke('download', {
  url: 'https://raw.githubusercontent.com/tauri-apps/tauri/dev/crates/tauri-schema-generator/schemas/config.schema.json',
  onEvent,
});
```
 ## Evaluating JavaScript To directly execute any JavaScript code on the webview context you can use the [`WebviewWindow#eval`](https://docs.rs/tauri/2.0.0/tauri/webview/struct.WebviewWindow.html#method.eval) function: src-tauri/src/lib.rs 
```rust
use tauri::Manager;


tauri::Builder::default()
  .setup(|app| {
    let webview = app.get_webview_window("main").unwrap();
    webview.eval("console.log('hello from Rust')")?;
    Ok(())
  })
```
 If the script to be evaluated is not so simple and must use input from Rust objects we recommend using the [serialize-to-javascript](https://docs.rs/serialize-to-javascript/latest/serialize_to_javascript/) crate.

# Calling Rust from the Frontend

This document includes guides on how to communicate with your Rust code from your application frontend. To see how to communicate with your frontend from your Rust code, see [Calling the Frontend from Rust](/develop/calling-frontend/). Tauri provides a [command](#commands) primitive for reaching Rust functions with type safety, along with an [event system](#event-system) that is more dynamic. ## Commands Tauri provides a simple yet powerful `command` system for calling Rust functions from your web app. Commands can accept arguments and return values. They can also return errors and be `async`. ### Basic Example Commands can be defined in your `src-tauri/src/lib.rs` file. To create a command, just add a function and annotate it with `#[tauri::command]`: src-tauri/src/lib.rs 
```rust
#[tauri::command]
fn my_custom_command() {
  println!("I was invoked from JavaScript!");
}
```
 Note Command names must be unique. Note Commands defined in the `lib.rs` file cannot be marked as `pub` due to a limitation in the glue code generation. You will see an error like this if you mark it as a public function: 
```plaintext
error[E0255]: the name `__cmd__command_name` is defined multiple times
  --> src/lib.rs:28:8
   |
27 | #[tauri::command]
   | ----------------- previous definition of the macro `__cmd__command_name` here
28 | pub fn x() {}
   |        ^ `__cmd__command_name` reimported here
   |
   = note: `__cmd__command_name` must be defined only once in the macro namespace of this module
```
 You will have to provide a list of your commands to the builder function like so: src-tauri/src/lib.rs 
```diff
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    +.invoke_handler(tauri::generate_handler![my_custom_command])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
```
 Now, you can invoke the command from your JavaScript code: 
```javascript
// When using the Tauri API npm package:
import { invoke } from '@tauri-apps/api/core';


// When using the Tauri global script (if not using the npm package)
// Be sure to set `app.withGlobalTauri` in `tauri.conf.json` to true
const invoke = window.__TAURI__.core.invoke;


// Invoke the command
invoke('my_custom_command');
```
 #### Defining Commands in a Separate Module If your application defines a lot of components or if they can be grouped, you can define commands in a separate module instead of bloating the `lib.rs` file. As an example let’s define a command in the `src-tauri/src/commands.rs` file: src-tauri/src/commands.rs 
```rust
#[tauri::command]
pub fn my_custom_command() {
  println!("I was invoked from JavaScript!");
}
```
 Note When defining commands in a separate module they should be marked as `pub`. Note The command name is not scoped to the module so they must be unique even between modules. In the `lib.rs` file, define the module and provide the list of your commands accordingly; src-tauri/src/lib.rs 
```diff
mod commands;


#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    +.invoke_handler(tauri::generate_handler![commands::my_custom_command])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
```
 Note the `commands::` prefix in the command list, which denotes the full path to the command function. The command name in this example is `my_custom_command` so you can still call it by executing `invoke("my_custom_command")` in your frontend, the `commands::` prefix is ignored. #### WASM When using a Rust frontend to call `invoke()` without arguments, you will need to adapt your frontend code as below. The reason is that Rust doesn’t support optional arguments. 
```diff
#[wasm_bindgen]
extern "C" {
    // invoke without arguments
+    #[wasm_bindgen(js_namespace = ["window", "__TAURI__", "core"], js_name = invoke)]
    +async fn invoke_without_args(cmd: &str) -> JsValue;


    // invoke with arguments (default)
    #[wasm_bindgen(js_namespace = ["window", "__TAURI__", "core"])]
    async fn invoke(cmd: &str, args: JsValue) -> JsValue;


    // They need to have different names!
}
```
 ### Passing Arguments Your command handlers can take arguments: 
```rust
#[tauri::command]
fn my_custom_command(invoke_message: String) {
  println!("I was invoked from JavaScript, with this message: {}", invoke_message);
}
```
 Arguments should be passed as a JSON object with camelCase keys: 
```javascript
invoke('my_custom_command', { invokeMessage: 'Hello!' });
```
 Note You can use `snake_case` for the arguments with the `rename_all` attribute: 
```rust
#[tauri::command(rename_all = "snake_case")]
fn my_custom_command(invoke_message: String) {}
```
 The corresponding JavaScript: 
```javascript
invoke('my_custom_command', { invoke_message: 'Hello!' });
```
 Arguments can be of any type, as long as they implement [`serde::Deserialize`](https://docs.serde.rs/serde/trait.Deserialize.html). ### Returning Data Command handlers can return data as well: 
```rust
#[tauri::command]
fn my_custom_command() -> String {
  "Hello from Rust!".into()
}
```
 The `invoke` function returns a promise that resolves with the returned value: 
```javascript
invoke('my_custom_command').then((message) => console.log(message));
```
 Returned data can be of any type, as long as it implements [`serde::Serialize`](https://docs.serde.rs/serde/trait.Serialize.html). #### Returning Array Buffers Return values that implements [`serde::Serialize`](https://docs.serde.rs/serde/trait.Serialize.html) are serialized to JSON when the response is sent to the frontend. This can slow down your application if you try to return a large data such as a file or a download HTTP response. To return array buffers in an optimized way, use [`tauri::ipc::Response`](https://docs.rs/tauri/2.0.0/tauri/ipc/struct.Response.html): 
```rust
use tauri::ipc::Response;
#[tauri::command]
fn read_file() -> Response {
  let data = std::fs::read("/path/to/file").unwrap();
  tauri::ipc::Response::new(data)
}
```
 ### Error Handling If your handler could fail and needs to be able to return an error, have the function return a `Result`: 
```rust
#[tauri::command]
fn login(user: String, password: String) -> Result<String, String> {
  if user == "tauri" && password == "tauri" {
    // resolve
    Ok("logged_in".to_string())
  } else {
    // reject
    Err("invalid credentials".to_string())
  }
}
```
 If the command returns an error, the promise will reject, otherwise, it resolves: 
```javascript
invoke('login', { user: 'tauri', password: '0j4rijw8=' })
  .then((message) => console.log(message))
  .catch((error) => console.error(error));
```
 As mentioned above, everything returned from commands must implement [`serde::Serialize`](https://docs.serde.rs/serde/trait.Serialize.html), including errors. This can be problematic if you’re working with error types from Rust’s std library or external crates as most error types do not implement it. In simple scenarios you can use `map_err` to convert these errors to `String`: 
```rust
#[tauri::command]
fn my_custom_command() -> Result<(), String> {
  std::fs::File::open("path/to/file").map_err(|err| err.to_string())?;
  // Return `null` on success
  Ok(())
}
```
 Since this is not very idiomatic you may want to create your own error type which implements `serde::Serialize`. In the following example, we use the [`thiserror`](https://github.com/dtolnay/thiserror) crate to help create the error type. It allows you to turn enums into error types by deriving the `thiserror::Error` trait. You can consult its documentation for more details. 
```rust
// create the error type that represents all errors possible in our program
#[derive(Debug, thiserror::Error)]
enum Error {
  #[error(transparent)]
  Io(#[from] std::io::Error)
}


// we must manually implement serde::Serialize
impl serde::Serialize for Error {
  fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
  where
    S: serde::ser::Serializer,
  {
    serializer.serialize_str(self.to_string().as_ref())
  }
}


#[tauri::command]
fn my_custom_command() -> Result<(), Error> {
  // This will return an error
  std::fs::File::open("path/that/does/not/exist")?;
  // Return `null` on success
  Ok(())
}
```
 A custom error type has the advantage of making all possible errors explicit so readers can quickly identify what errors can happen. This saves other people (and yourself) enormous amounts of time when reviewing and refactoring code later.\ It also gives you full control over the way your error type gets serialized. In the above example, we simply returned the error message as a string, but you could assign each error a code so you could more easily map it to a similar looking TypeScript error enum for example: 
```rust
#[derive(Debug, thiserror::Error)]
enum Error {
  #[error(transparent)]
  Io(#[from] std::io::Error),
  #[error("failed to parse as string: {0}")]
  Utf8(#[from] std::str::Utf8Error),
}


#[derive(serde::Serialize)]
#[serde(tag = "kind", content = "message")]
#[serde(rename_all = "camelCase")]
enum ErrorKind {
  Io(String),
  Utf8(String),
}


impl serde::Serialize for Error {
  fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
  where
    S: serde::ser::Serializer,
  {
    let error_message = self.to_string();
    let error_kind = match self {
      Self::Io(_) => ErrorKind::Io(error_message),
      Self::Utf8(_) => ErrorKind::Utf8(error_message),
    };
    error_kind.serialize(serializer)
  }
}


#[tauri::command]
fn read() -> Result<Vec<u8>, Error> {
  let data = std::fs::read("/path/to/file")?;
  Ok(data)
}
```
 In your frontend you now get a `{ kind: 'io' | 'utf8', message: string }` error object: 
```ts
type ErrorKind = {
  kind: 'io' | 'utf8';
  message: string;
};


invoke('read').catch((e: ErrorKind) => {});
```
 ### Async Commands Asynchronous commands are preferred in Tauri to perform heavy work in a manner that doesn’t result in UI freezes or slowdowns. Note Async commands are executed on a separate async task using [`async_runtime::spawn`](https://docs.rs/tauri/2.0.0/tauri/async_runtime/fn.spawn.html). Commands without the *async* keyword are executed on the main thread unless defined with *#\[tauri::command(async)]*. **If your command needs to run asynchronously, simply declare it as `async`.** Caution You need to be careful when creating asynchronous functions using Tauri. Currently, you cannot simply include borrowed arguments in the signature of an asynchronous function. Some common examples of types like this are `&str` and `State<'_, Data>`. This limitation is tracked here: <https://github.com/tauri-apps/tauri/issues/2533> and workarounds are shown below. When working with borrowed types, you have to make additional changes. These are your two main options: **Option 1**: Convert the type, such as `&str` to a similar type that is not borrowed, such as `String`. This may not work for all types, for example `State<'_, Data>`. *Example:* 
```rust
// Declare the async function using String instead of &str, as &str is borrowed and thus unsupported
#[tauri::command]
async fn my_custom_command(value: String) -> String {
  // Call another async function and wait for it to finish
  some_async_function().await;
  value
}
```
 **Option 2**: Wrap the return type in a [`Result`](https://doc.rust-lang.org/std/result/index.html). This one is a bit harder to implement, but works for all types. Use the return type `Result<a, b>`, replacing `a` with the type you wish to return, or `()` if you wish to return `null`, and replacing `b` with an error type to return if something goes wrong, or `()` if you wish to have no optional error returned. For example: * `Result<String, ()>` to return a String, and no error. * `Result<(), ()>` to return `null`. * `Result<bool, Error>` to return a boolean or an error as shown in the [Error Handling](#error-handling) section above. *Example:* 
```rust
// Return a Result<String, ()> to bypass the borrowing issue
#[tauri::command]
async fn my_custom_command(value: &str) -> Result<String, ()> {
  // Call another async function and wait for it to finish
  some_async_function().await;
  // Note that the return value must be wrapped in `Ok()` now.
  Ok(format!(value))
}
```
 ##### Invoking from JavaScript Since invoking the command from JavaScript already returns a promise, it works just like any other command: 
```javascript
invoke('my_custom_command', { value: 'Hello, Async!' }).then(() =>
  console.log('Completed!')
);
```
 ### Channels The Tauri channel is the recommended mechanism for streaming data such as streamed HTTP responses to the frontend. The following example reads a file and notifies the frontend of the progress in chunks of 4096 bytes: 
```rust
use tokio::io::AsyncReadExt;


#[tauri::command]
async fn load_image(path: std::path::PathBuf, reader: tauri::ipc::Channel<&[u8]>) {
  // for simplicity this example does not include error handling
  let mut file = tokio::fs::File::open(path).await.unwrap();


  let mut chunk = vec![0; 4096];


  loop {
    let len = file.read(&mut chunk).await.unwrap();
    if len == 0 {
      // Length of zero means end of file.
      break;
    }
    reader.send(&chunk).unwrap();
  }
}
```
 See the [channels documentation](/develop/calling-frontend/#channels) for more information. ### Accessing the WebviewWindow in Commands Commands can access the `WebviewWindow` instance that invoked the message: src-tauri/src/lib.rs 
```rust
#[tauri::command]
async fn my_custom_command(webview_window: tauri::WebviewWindow) {
  println!("WebviewWindow: {}", webview_window.label());
}
```
 ### Accessing an AppHandle in Commands Commands can access an `AppHandle` instance: src-tauri/src/lib.rs 
```rust
#[tauri::command]
async fn my_custom_command(app_handle: tauri::AppHandle) {
  let app_dir = app_handle.path().app_dir();
  use tauri::GlobalShortcutManager;
  app_handle.global_shortcut_manager().register("CTRL + U", move || {});
}
```
 ### Accessing Managed State Tauri can manage state using the `manage` function on `tauri::Builder`. The state can be accessed on a command using `tauri::State`: src-tauri/src/lib.rs 
```rust
struct MyState(String);


#[tauri::command]
fn my_custom_command(state: tauri::State<MyState>) {
  assert_eq!(state.0 == "some state value", true);
}


#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .manage(MyState("some state value".into()))
    .invoke_handler(tauri::generate_handler![my_custom_command])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
```
 ### Accessing Raw Request Tauri commands can also access the full [`tauri::ipc::Request`](https://docs.rs/tauri/2.0.0/tauri/ipc/struct.Request.html) object which includes the raw body payload and the request headers. 
```rust
#[derive(Debug, thiserror::Error)]
enum Error {
  #[error("unexpected request body")]
  RequestBodyMustBeRaw,
  #[error("missing `{0}` header")]
  MissingHeader(&'static str),
}


impl serde::Serialize for Error {
  fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
  where
    S: serde::ser::Serializer,
  {
    serializer.serialize_str(self.to_string().as_ref())
  }
}


#[tauri::command]
fn upload(request: tauri::ipc::Request) -> Result<(), Error> {
  let tauri::ipc::InvokeBody::Raw(upload_data) = request.body() else {
    return Err(Error::RequestBodyMustBeRaw);
  };
  let Some(authorization_header) = request.headers().get("Authorization") else {
    return Err(Error::MissingHeader("Authorization"));
  };


  // upload...


  Ok(())
}
```
 In the frontend you can call invoke() sending a raw request body by providing an ArrayBuffer or Uint8Array on the payload argument, and include request headers in the third argument: 
```js
const data = new Uint8Array([1, 2, 3]);
await __TAURI__.core.invoke('upload', data, {
  headers: {
    Authorization: 'apikey',
  },
});
```
 ### Creating Multiple Commands The `tauri::generate_handler!` macro takes an array of commands. To register multiple commands, you cannot call invoke_handler multiple times. Only the last call will be used. You must pass each command to a single call of `tauri::generate_handler!`. src-tauri/src/lib.rs 
```rust
#[tauri::command]
fn cmd_a() -> String {
  "Command a"
}
#[tauri::command]
fn cmd_b() -> String {
  "Command b"
}


#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![cmd_a, cmd_b])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
```
 ### Complete Example Any or all of the above features can be combined: src-tauri/src/lib.rs 
```rust
struct Database;


#[derive(serde::Serialize)]
struct CustomResponse {
  message: String,
  other_val: usize,
}


async fn some_other_function() -> Option<String> {
  Some("response".into())
}


#[tauri::command]
async fn my_custom_command(
  window: tauri::WebviewWindow,
  number: usize,
  database: tauri::State<'_, Database>,
) -> Result<CustomResponse, String> {
  println!("Called from {}", window.label());
  let result: Option<String> = some_other_function().await;
  if let Some(message) = result {
    Ok(CustomResponse {
      message,
      other_val: 42 + number,
    })
  } else {
    Err("No result".into())
  }
}


#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .manage(Database {})
    .invoke_handler(tauri::generate_handler![my_custom_command])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
```
 
```javascript
import { invoke } from '@tauri-apps/api/core';


// Invocation from JavaScript
invoke('my_custom_command', {
  number: 42,
})
  .then((res) =>
    console.log(`Message: ${res.message}, Other Val: ${res.other_val}`)
  )
  .catch((e) => console.error(e));
```
 ## Event System The event system is a simpler communication mechanism between your frontend and the Rust. Unlike commands, events are not type safe, are always async, cannot return values and only supports JSON payloads. ### Global Events To trigger a global event you can use the [event.emit](/reference/javascript/api/namespaceevent/#emit) or the [WebviewWindow#emit](/reference/javascript/api/namespacewebviewwindow/#emit) functions: 
```js
import { emit } from '@tauri-apps/api/event';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';


// emit(eventName, payload)
emit('file-selected', '/path/to/file');


const appWebview = getCurrentWebviewWindow();
appWebview.emit('route-changed', { url: window.location.href });
```
 Note Global events are delivered to **all** listeners ### Webview Event To trigger an event to a listener registered by a specific webview you can use the [event.emitTo](/reference/javascript/api/namespaceevent/#emitto) or the [WebviewWindow#emitTo](/reference/javascript/api/namespacewebviewwindow/#emitto) functions: 
```js
import { emitTo } from '@tauri-apps/api/event';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';


// emitTo(webviewLabel, eventName, payload)
emitTo('settings', 'settings-update-requested', {
  key: 'notification',
  value: 'all',
});


const appWebview = getCurrentWebviewWindow();
appWebview.emitTo('editor', 'file-changed', {
  path: '/path/to/file',
  contents: 'file contents',
});
```
 Note Webview-specific events are **not** triggered to regular global event listeners. To listen to **any** event you must provide the `{ target: { kind: 'Any' } }` option to the [event.listen](/reference/javascript/api/namespaceevent/#listen) function, which defines the listener to act as a catch-all for emitted events: 
```js
import { listen } from '@tauri-apps/api/event';
listen(
  'state-changed',
  (event) => {
    console.log('got state changed event', event);
  },
  {
    target: { kind: 'Any' },
  }
);
```
 ### Listening to Events The `@tauri-apps/api` NPM package offers APIs to listen to both global and webview-specific events. * Listening to global events 
  ```ts
  import { listen } from '@tauri-apps/api/event';


  type DownloadStarted = {
    url: string;
    downloadId: number;
    contentLength: number;
  };


  listen<DownloadStarted>('download-started', (event) => {
    console.log(
      `downloading ${event.payload.contentLength} bytes from ${event.payload.url}`
    );
  });
  ```
 * Listening to webview-specific events 
  ```ts
  import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';


  const appWebview = getCurrentWebviewWindow();
  appWebview.listen<string>('logged-in', (event) => {
    localStorage.setItem('session-token', event.payload);
  });
  ```
 The `listen` function keeps the event listener registered for the entire lifetime of the application. To stop listening on an event you can use the `unlisten` function which is returned by the `listen` function: 
```js
import { listen } from '@tauri-apps/api/event';


const unlisten = await listen('download-started', (event) => {});
unlisten();
```
 Note Always use the unlisten function when your execution context goes out of scope such as when a component is unmounted. When the page is reloaded or you navigate to another URL the listeners are unregistered automatically. This does not apply to a Single Page Application (SPA) router though. #### Common Pitfalls ##### Don’t call `unlisten()` before the listener resolves The `listen` function returns a Promise that resolves to the `unlisten` handle. If you call `unlisten` synchronously before the Promise resolves, the handler will be removed immediately and you won’t receive any events: 
```js
// Wrong: unlisten is called before the listener is registered
const unlisten = listen('sync-complete', (event) => {
  console.log('sync finished');
});
unlisten(); // unlisten is a Promise here, not a function -- the listener is not cleaned up


// Correct: await the Promise to get the unlisten handle
const unlisten = await listen('sync-complete', (event) => {
  console.log('sync finished');
});
// Now you can store and call it later, e.g. in a cleanup function
unlisten();
```
 ##### Timing in setup hooks In frameworks like React, Vue, and Svelte, the setup or mount hook runs before the component is fully rendered. If you listen for events during setup, make sure the event handler does not depend on DOM elements that haven’t been rendered yet, or defer the listener registration to an effect/hook that runs after mount. 
```js
// Wrong: DOM ref may not be available yet
function MyComponent() {
  const ref = useRef(null);
  listen('scroll-to', (event) => {
    ref.current.scrollIntoView(); // ref.current may be null during setup
  });
  return <div ref={ref} />;
}


// Correct: use useEffect which runs after the component mounts
function MyComponent() {
  const ref = useRef(null);
  useEffect(() => {
    const unlisten = listen('scroll-to', (event) => {
      ref.current?.scrollIntoView();
    });
    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);
  return <div ref={ref} />;
}
```
 ##### Event ordering and async listeners Event listeners are called in the order they are registered, but if a listener is async and the event emitter sends multiple events in rapid succession, the listeners may process events out of order. For ordered, high-throughput data delivery, consider using [Channels](/develop/calling-frontend/#channels) instead of the event system. #### Framework-specific Cleanup Examples When using a frontend framework, you should clean up event listeners when a component is unmounted to avoid memory leaks and duplicate handlers. * React 
  ```tsx
  import { useEffect, useState } from 'react';
  import { listen } from '@tauri-apps/api/event';


  function DownloadTracker() {
    const [progress, setProgress] = useState(0);


    useEffect(() => {
      const unlisten = listen<number>('download-progress', (event) => {
        setProgress(event.payload);
      });


      return () => {
        unlisten.then((fn) => fn());
      };
    }, []);


    return <div>Download progress: {progress}%</div>;
  }
  ```
 * Vue 
  ```vue
  <script setup lang="ts">
  import { ref, onMounted, onUnmounted } from 'vue';
  import { listen } from '@tauri-apps/api/event';


  const progress = ref(0);
  let unlistenPromise;


  onMounted(() => {
    unlistenPromise = listen<number>('download-progress', (event) => {
      progress.value = event.payload;
    });
  });


  onUnmounted(() => {
    unlistenPromise?.then((fn) => fn());
  });
  </script>


  <template>
    <div>Download progress: {{ progress }}%</div>
  </template>
  ```
 * Svelte 
  ```svelte
  <script lang="ts">
  import { listen } from '@tauri-apps/api/event';


  let progress = $state(0);


  $effect(() => {
    const unlistenPromise = listen<number>(
      'download-progress',
      (event) => {
        progress = event.payload;
      }
    );


    return () => {
      unlistenPromise.then((unlisten) => unlisten());
    };
  });
  </script>


  <div>Download progress: {progress}%</div>
  ```
 Additionally Tauri provides a utility function for listening to an event exactly once: 
```js
import { once } from '@tauri-apps/api/event';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';


once('ready', (event) => {});


const appWebview = getCurrentWebviewWindow();
appWebview.once('ready', () => {});
```
 Note Events emitted in the frontend also trigger listeners registered by these APIs. For more information, see the [Calling Rust from the Frontend](/develop/calling-rust/) documentation. #### Listening to Events on Rust Global and webview-specific events are also delivered to listeners registered in Rust. * Listening to global events src-tauri/src/lib.rs 
  ```rust
  use tauri::Listener;


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
    tauri::Builder::default()
      .setup(|app| {
        app.listen("download-started", |event| {
          if let Ok(payload) = serde_json::from_str::<DownloadStarted>(&event.payload()) {
            println!("downloading {}", payload.url);
          }
        });
        Ok(())
      })
      .run(tauri::generate_context!())
      .expect("error while running tauri application");
  }
  ```
 * Listening to webview-specific events src-tauri/src/lib.rs 
  ```rust
  use tauri::{Listener, Manager};


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
    tauri::Builder::default()
      .setup(|app| {
        let webview = app.get_webview_window("main").unwrap();
        webview.listen("logged-in", |event| {
          let session_token = event.data;
          // save token..
        });
        Ok(())
      })
      .run(tauri::generate_context!())
      .expect("error while running tauri application");
  }
  ```
 The `listen` function keeps the event listener registered for the entire lifetime of the application. To stop listening on an event you can use the `unlisten` function: 
```rust
// unlisten outside of the event handler scope:
let event_id = app.listen("download-started", |event| {});
app.unlisten(event_id);


// unlisten when some event criteria is matched
let handle = app.handle().clone();
app.listen("status-changed", |event| {
  if event.data == "ready" {
    handle.unlisten(event.id);
  }
});
```
 Additionally Tauri provides a utility function for listening to an event exactly once: 
```rust
app.once("ready", |event| {
  println!("app is ready");
});
```
 In this case the event listener is immediately unregistered after its first trigger. To learn how to listen to events and emit events from your Rust code, see the [Rust Event System documentation](/develop/calling-frontend/#event-system).

# Configuration Files

Since Tauri is a toolkit for building applications there can be many files to configure project settings. Some common files that you may run across are `tauri.conf.json`, `package.json` and `Cargo.toml`. We briefly explain each on this page to help point you in the right direction for which files to modify. ## Tauri Config The Tauri configuration is used to define the source of your Web app, describe your application’s metadata, configure bundles, set plugin configurations, modify runtime behavior by configuring windows, tray icons, menus and more. This file is used by the Tauri runtime and the Tauri CLI. You can define build settings (such as the [command run before `tauri build`](/reference/config/#beforebuildcommand) or [`tauri dev`](/reference/config/#beforedevcommand-1) kicks in), set the [name](/reference/config/#productname) and [version of your app](/reference/config/#version), [control the Tauri runtime](/reference/config/#appconfig), and [configure plugins](/reference/config/#plugins). ### Supported Formats The default Tauri config format is JSON. The JSON5 or TOML format can be enabled by adding the `config-json5` or `config-toml` feature flag (respectively) to the `tauri` and `tauri-build` dependencies in `Cargo.toml`. Cargo.toml 
```toml
[build-dependencies]
tauri-build = { version = "2.0.0", features = [ "config-json5" ] }


[dependencies]
tauri = { version = "2.0.0", features = [  "config-json5" ] }
```
 The structure and values are the same across all formats, however, the formatting should be consistent with the respective file’s format: tauri.conf.json 
```json5
{
  build: {
    devUrl: 'http://localhost:3000',
    // start the dev server
    beforeDevCommand: 'npm run dev',
  },
  bundle: {
    active: true,
    icon: ['icons/app.png'],
  },
  app: {
    windows: [
      {
        title: 'MyApp',
      },
    ],
  },
  plugins: {
    updater: {
      pubkey: 'updater pub key',
      endpoints: ['https://my.app.updater/{{target}}/{{current_version}}'],
    },
  },
}
```
 Tauri.toml 
```toml
[build]
dev-url = "http://localhost:3000"
# start the dev server
before-dev-command = "npm run dev"


[bundle]
active = true
icon = ["icons/app.png"]


[[app.windows]]
title = "MyApp"


[plugins.updater]
pubkey = "updater pub key"
endpoints = ["https://my.app.updater/{{target}}/{{current_version}}"]
```
 Note that JSON5 and TOML supports comments, and TOML can use kebab-case for config names which are more idiomatic. Field names are case-sensitive in all 3 formats. ### Platform-specific Configuration In addition to the default configuration file, Tauri can read a platform-specific configuration from: * `tauri.linux.conf.json` or `Tauri.linux.toml` for Linux * `tauri.windows.conf.json` or `Tauri.windows.toml` for Windows * `tauri.macos.conf.json` or `Tauri.macos.toml` for macOS * `tauri.android.conf.json` or `Tauri.android.toml` for Android * `tauri.ios.conf.json` or `Tauri.ios.toml` for iOS The platform-specific configuration file gets merged with the main configuration object following the [JSON Merge Patch (RFC 7396)](https://datatracker.ietf.org/doc/html/rfc7396) specification. Note Objects are merged key by key, but arrays are replaced as a whole, including arrays nested in objects. In the example below `bundle` is merged, while `bundle.resources` is replaced: the platform-specific entries do not extend the base list, they take its place. The same holds when the array elements are objects, such as `app.windows`. A platform-specific entry replaces the base entry rather than merging into it, so any field you omit falls back to its default instead of the value in your base configuration. Repeat everything you want to keep. For example, given the following base `tauri.conf.json`: tauri.conf.json 
```json
{
  "productName": "MyApp",
  "bundle": {
    "resources": ["./resources", "./shared-assets"]
  },
  "plugins": {
    "deep-link": {}
  }
}
```
 And the given `tauri.linux.conf.json`: tauri.linux.conf.json 
```json
{
  "productName": "my-app",
  "bundle": {
    "resources": ["./linux-assets"]
  },
  "plugins": {
    "cli": {
      "description": "My app",
      "subcommands": {
        "update": {}
      }
    },
    "deep-link": {}
  }
}
```
 The resolved configuration for Linux would be the following object: 
```json
{
  "productName": "my-app",
  "bundle": {
    "resources": ["./linux-assets"]
  },
  "plugins": {
    "cli": {
      "description": "My app",
      "subcommands": {
        "update": {}
      }
    },
    "deep-link": {}
  }
}
```
 Additionally you can provide a configuration to be merged via the CLI, see the following section for more information. ### Extending the Configuration The Tauri CLI allows you to extend the Tauri configuration when running one of the `dev`, `android dev`, `ios dev`, `build`, `android build`, `ios build` or `bundle` commands. The configuration extension can be provided by the `--config` argument either as a raw JSON string or as a path to a JSON file. Tauri uses the [JSON Merge Patch (RFC 7396)](https://datatracker.ietf.org/doc/html/rfc7396) specification to merge the provided configuration value with the originally resolved configuration object. This mechanism can be used to define multiple flavours of your application or have more flexibility when configuring your application bundles. For instance to distribute a completely isolated *beta* application you can use this feature to configure a separate application name and identifier: src-tauri/tauri.beta.conf.json 
```json
{
  "productName": "My App Beta",
  "identifier": "com.myorg.myappbeta"
}
```
 And to distribute this separate *beta* app you provide this configuration file when building it: * npm 
  ```sh
  npm run tauri build -- --config src-tauri/tauri.beta.conf.json
  ```
 * yarn 
  ```sh
  yarn tauri build --config src-tauri/tauri.beta.conf.json
  ```
 * pnpm 
  ```sh
  pnpm tauri build --config src-tauri/tauri.beta.conf.json
  ```
 * deno 
  ```sh
  deno task tauri build --config src-tauri/tauri.beta.conf.json
  ```
 * bun 
  ```sh
  bun tauri build --config src-tauri/tauri.beta.conf.json
  ```
 * cargo 
  ```sh
  cargo tauri build --config src-tauri/tauri.beta.conf.json
  ```
 ## `Cargo.toml` Cargo’s manifest file is used to declare Rust crates your app depends on, metadata about your app, and other Rust-related features. If you do not intend to do backend development using Rust for your app then you may not be modifying it much, but it’s important to know that it exists and what it does. Below is an example of a barebones `Cargo.toml` file for a Tauri project: Cargo.toml 
```toml
[package]
name = "app"
version = "0.1.0"
description = "A Tauri App"
authors = ["you"]
license = ""
repository = ""
default-run = "app"
edition = "2021"
rust-version = "1.57"


[build-dependencies]
tauri-build = { version = "2.0.0" }


[dependencies]
serde_json = "1.0"
serde = { version = "1.0", features = ["derive"] }
tauri = { version = "2.0.0", features = [ ] }
```
 The most important parts to take note of are the `tauri-build` and `tauri` dependencies. Generally, they must both be on the same latest minor versions as the Tauri CLI, but this is not strictly required. If you encounter issues while trying to run your app you should check that any Tauri versions (`tauri` and `tauri-cli`) are on the latest versions for their respective minor releases. Cargo version numbers use [Semantic Versioning](https://semver.org). Running `cargo update` in the `src-tauri` folder will pull the latest available Semver-compatible versions of all dependencies. For example, if you specify `2.0.0` as the version for `tauri-build`, Cargo will detect and download version `2.0.1` because it is the latest Semver-compatible version available. Tauri will update the major version number whenever a breaking change is introduced, meaning you should always be capable of safely upgrading to the latest minor and patch versions without fear of your code breaking. If you want to use a specific crate version you can use exact versions instead by prepending `=` to the version number of the dependency: 
```plaintext
tauri-build = { version = "=2.0.0" }
```
 An additional thing to take note of is the `features=[]` portion of the `tauri` dependency. Running `tauri dev` and `tauri build` will automatically manage which features need to be enabled in your project based on the your Tauri configuration. For more information about `tauri` feature flags see the [documentation](https://docs.rs/tauri/2.0.0/tauri/#cargo-features). When you build your application a `Cargo.lock` file is produced. This file is used primarily for ensuring that the same dependencies are used across machines during development (similar to `yarn.lock`, `pnpm-lock.yaml` or `package-lock.json` in Node.js). It is recommended to commit this file to your source repository so you get consistent builds. To learn more about the Cargo manifest file please refer to the [official documentation](https://doc.rust-lang.org/cargo/reference/manifest.html). ## `package.json` This is the package file used by Node.js. If the frontend of your Tauri app is developed using Node.js-based technologies (such as `npm`, `yarn`, or `pnpm`) this file is used to configure the frontend dependencies and scripts. An example of a barebones `package.json` file for a Tauri project might look a little something like this: package.json 
```json
{
  "scripts": {
    "dev": "command to start your app development mode",
    "build": "command to build your app frontend",
    "tauri": "tauri"
  },
  "dependencies": {
    "@tauri-apps/api": "^2.0.0",
    "@tauri-apps/cli": "^2.0.0"
  }
}
```
 It’s common to use the `"scripts"` section to store the commands used to launch and build the frontend used by your Tauri application. The above `package.json` file specifies the `dev` command that you can run using `yarn dev` or `npm run dev` to start the frontend framework and the `build` command that you can run using `yarn build` or `npm run build` to build your frontend’s Web assets to be added by Tauri in production. The most convenient way to use these scripts is to hook them with the Tauri CLI via the Tauri configuration’s [beforeDevCommand](/reference/config/#beforedevcommand-1) and [beforeBuildCommand](/reference/config/#beforebuildcommand) hooks: tauri.conf.json 
```json
{
  "build": {
    "beforeDevCommand": "yarn dev",
    "beforeBuildCommand": "yarn build"
  }
}
```
 Note The `"tauri"` script is only needed when using `npm` The dependencies object specifies which dependencies Node.js should download when you run either `yarn`, `pnpm install` or `npm install` (in this case the Tauri CLI and API). In addition to the `package.json` file you may see either a `yarn.lock`, `pnpm-lock.yaml` or `package-lock.json` file. These files assist in ensuring that when you download the dependencies later you’ll get the exact same versions that you have used during development (similar to `Cargo.lock` in Rust). To learn more about the `package.json` file format please refer to the [official documentation](https://docs.npmjs.com/cli/v8/configuring-npm/package-json).

# Debug

With all the moving pieces in Tauri, you may run into a problem that requires debugging. There are many locations where error details are printed, and Tauri includes some tools to make the debugging process more straightforward. ## Development Only Code One of the most useful tools in your toolkit for debugging is the ability to add debugging statements in your code. However, you generally don’t want these to end up in production, which is where the ability to check whether you’re running in development mode or not comes in handy. ### In Rust 
```rs
fn main() {
  // Whether the current instance was started with `tauri dev` or not.
  #[cfg(dev)]
  {
    // `tauri dev` only code
  }
  if cfg!(dev) {
    // `tauri dev` only code
  } else {
    // `tauri build` only code
  }
  let is_dev: bool = tauri::is_dev();


  // Whether debug assertions are enabled or not. This is true for `tauri dev` and `tauri build --debug`.
  #[cfg(debug_assertions)]
  {
    // Debug only code
  }
  if cfg!(debug_assertions) {
    // Debug only code
  } else {
    // Production only code
  }
}
```
 ## Rust Console The first place to look for errors is in the Rust Console. This is in the terminal where you ran, e.g., `tauri dev`. You can use the following code to print something to that console from within a Rust file: 
```rust
println!("Message from Rust: {}", msg);
```
 Sometimes you may have an error in your Rust code, and the Rust compiler can give you lots of information. If, for example, `tauri dev` crashes, you can rerun it like this on Linux and macOS: 
```shell
RUST_BACKTRACE=1 tauri dev
```
 or like this on Windows (PowerShell): 
```powershell
$env:RUST_BACKTRACE=1
tauri dev
```
 This command gives you a granular stack trace. Generally speaking, the Rust compiler helps you by giving you detailed information about the issue, such as: 
```bash
error[E0425]: cannot find value `sun` in this scope
  --> src/main.rs:11:5
   |
11 |     sun += i.to_string().parse::<u64>().unwrap();
   |     ^^^ help: a local variable with a similar name exists: `sum`


error: aborting due to previous error


For more information about this error, try `rustc --explain E0425`.
```
 ## WebView Console Right-click in the WebView, and choose `Inspect Element`. This opens up a web-inspector similar to the Chrome or Firefox dev tools you are used to. You can also use the `Ctrl + Shift + i` shortcut on Linux and Windows, and `Command + Option + i` on macOS to open the inspector. The inspector is platform-specific, rendering the webkit2gtk WebInspector on Linux, Safari’s inspector on macOS and the Microsoft Edge DevTools on Windows. ### Opening Devtools Programmatically You can control the inspector window visibility by using the [`WebviewWindow::open_devtools`](https://docs.rs/tauri/2.0.0/tauri/webview/struct.WebviewWindow.html#method.open_devtools) and [`WebviewWindow::close_devtools`](https://docs.rs/tauri/2.0.0/tauri/webview/struct.WebviewWindow.html#method.close_devtools) functions: 
```rust
tauri::Builder::default()
  .setup(|app| {
    #[cfg(debug_assertions)] // only include this code on debug builds
    {
      let window = app.get_webview_window("main").unwrap();
      window.open_devtools();
      window.close_devtools();
    }
    Ok(())
  });
```
 ### Using the Inspector in Production By default, the inspector is only enabled in development and debug builds unless you enable it with a Cargo feature. #### Create a Debug Build To create a debug build, run the `tauri build --debug` command. * npm 
  ```sh
  npm run tauri build -- --debug
  ```
 * yarn 
  ```sh
  yarn tauri build --debug
  ```
 * pnpm 
  ```sh
  pnpm tauri build --debug
  ```
 * deno 
  ```sh
  deno task tauri build --debug
  ```
 * bun 
  ```sh
  bun tauri build --debug
  ```
 * cargo 
  ```sh
  cargo tauri build --debug
  ```
 Like the normal build and dev processes, building takes some time the first time you run this command but is significantly faster on subsequent runs. The final bundled app has the development console enabled and is placed in `src-tauri/target/debug/bundle`. You can also run a built app from the terminal, giving you the Rust compiler notes (in case of errors) or your `println` messages. Browse to the file `src-tauri/target/(release|debug)/[app name]` and run it directly in your console or double-click the executable itself in the filesystem (note: the console closes on errors with this method). ##### Enable Devtools Feature Danger The devtools API is private on macOS. Using private APIs on macOS prevents your application from being accepted to the App Store. To enable the devtools in **production builds**, you must enable the `devtools` Cargo feature in the `src-tauri/Cargo.toml` file: 
```toml
[dependencies]
tauri = { version = "...", features = ["...", "devtools"] }
```
 ## Debugging the Core Process The Core process is powered by Rust so you can use GDB or LLDB to debug it. You can follow the [Debugging in VS Code](/develop/debug/vscode/) guide to learn how to use the LLDB VS Code Extension to debug the Core Process of Tauri applications.

# CrabNebula DevTools

[CrabNebula](https://crabnebula.dev/) provides a free [DevTools](https://crabnebula.dev/devtools/) application for Tauri as part of its partnership with the Tauri project. This application allows you to instrument your Tauri app by capturing its embedded assets, Tauri configuration file, logs and spans and providing a web frontend to seamlessly visualize data in real time. With the CrabNebula DevTools you can inspect your app’s log events (including logs from dependencies), track down the performance of your command calls and overall Tauri API usage, with a special interface for Tauri events and commands, including payload, responses and inner logs and execution spans. To enable the CrabNebula DevTools, install the devtools crate: 
```sh
cargo add tauri-plugin-devtools@2.0.0
```
 And initialize the plugin as soon as possible in your main function: 
```rust
fn main() {
    // This should be called as early in the execution of the app as possible
    #[cfg(debug_assertions)] // only enable instrumentation in development builds
    let devtools = tauri_plugin_devtools::init();


    let mut builder = tauri::Builder::default();


    #[cfg(debug_assertions)]
    {
        builder = builder.plugin(devtools);
    }


    builder
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```
 And then run your app as usual, if everything is set up correctly devtools will print the following message: ![DevTools message on terminal](/_astro/crabnebula-devtools.7F1z87oz_Z1ikk1h.webp) Note In this case we only initialize the devtools plugin for debug applications, which is recommended. For more information, see the [CrabNebula DevTools](https://docs.crabnebula.dev/devtools/get-started/) documentation.

# Linux Graphics Issues

On Linux, Tauri renders through WebKitGTK. On some setups, most often NVIDIA GPUs, WebKitGTK and the graphics driver disagree and you get anything from a blank window to subtle rendering problems. This page collects the known symptoms and workarounds. See [tauri-apps/tauri#9394](https://github.com/tauri-apps/tauri/issues/9394) for the original reports. ## Common symptoms * The window opens but stays blank or white. * The window flickers, especially while resizing. * The app dies on resize with no useful error output. * Console shows `AcceleratedSurfaceDMABuf was unable to construct a complete framebuffer`. * Console shows `Gdk-Message: Error 71 (Protocol error) dispatching to Wayland display.` Most of these come from the WebKitGTK DMABUF renderer requesting buffer formats the NVIDIA driver does not provide. See the [WebKitGTK bug tracker](https://bugs.webkit.org/show_bug.cgi?id=261874) and the [NVIDIA forums](https://forums.developer.nvidia.com/t/geforce-rtx-4070-flickering-issue-when-using-the-dmabuf-renderer-in-webkitgtk/274741) for upstream discussion. ## Workarounds Try these in order. The earlier ones keep hardware acceleration. 1. Make sure kernel mode setting is on. NVIDIA drivers older than 545 often need `nvidia_drm.modeset=1` as a kernel parameter. 2. Set `__NV_DISABLE_EXPLICIT_SYNC=1`. This often fixes the Wayland `Error 71` crash without a performance cost. 3. Set `WEBKIT_DISABLE_DMABUF_RENDERER=1`. Fixes the DMABUF framebuffer error and the `Error 71` crash, at the cost of the faster rendering path. 4. Set `WEBKIT_DISABLE_COMPOSITING_MODE=1`. Last resort for the silent crash on resize. This disables accelerated compositing entirely. You can set these in your shell to test, or set them in `main()` before the webview is created so users do not have to: 
```rust
fn main() {
  // Workaround for WebKitGTK on NVIDIA, see tauri-apps/tauri#9394
  #[cfg(target_os = "linux")]
  std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");


  tauri::Builder::default()
    // ...
}
```
 Only ship an unconditional override like this if you have verified your app is affected. It disables a faster path for everyone, including users on working setups. ## Silent failures: WebGL and canvas Not every problem crashes or shows an error. WebGL and canvas content can silently land on a slow path while the rest of the app looks fine. Two things make this hard to detect from inside your frontend: * WebGL2 context creation succeeds even when the result is backed by a software rasterizer or a slow presentation path. There is no error to catch. * WebKitGTK masks the WebGL renderer string for fingerprinting protection. `WEBGL_debug_renderer_info` reports `Apple GPU` on every Linux machine, so you cannot check what is actually behind the context. In practice this shows up as high input latency or low frame rates in WebGL heavy views (terminal emulators, editors, maps, charts), while the same code is fast in a regular browser. If your app has a WebGL rendering path, give it a non WebGL fallback on Linux and consider exposing a setting so users can switch, instead of trusting the context to tell you.

# Debug in Neovim

There are many different plugins that can be used to debug Rust code in Neovim. This guide will show you how to set up `nvim-dap` and some additional plugins to debug Tauri application. ### Prerequisites `nvim-dap` extension requires `codelldb` binary. Download the version for your system from <https://github.com/vadimcn/codelldb/releases> and unzip it. We will point to it later in the `nvim-dap` configuration. ### Configuring nvim-dap Install [`nvim-dap`](https://github.com/mfussenegger/nvim-dap) and [`nvim-dap-ui`](https://github.com/rcarriga/nvim-dap-ui) plugins. Follow the instructions provided on their github pages or simply use your favourite plugin manager. Note that `nvim-dap-ui` requires `nvim-nio` plugin. Next, setup the plugin in your Neovim configuration: init.lua 
```lua
local dap = require("dap")


dap.adapters.codelldb = {
  type = 'server',
  port = "${port}",
  executable = {
    -- Change this to your path!
    command = '/opt/codelldb/adapter/codelldb',
    args = {"--port", "${port}"},
  }
}


dap.configurations.rust= {
  {
    name = "Launch file",
    type = "codelldb",
    request = "launch",
    program = function()
      return vim.fn.input('Path to executable: ', vim.fn.getcwd() .. '/target/debug/', 'file')
    end,
    cwd = '${workspaceFolder}',
    stopOnEntry = false
  },
}
```
 This setup will ask you to point to the Tauri App binary you want to debug each time you launch the debugger. Optionally, you can setup `nvim-dap-ui` plugin to toggle debugger view automatically each time debugging session starts and stops: init.lua 
```lua
local dapui = require("dapui")
dapui.setup()


dap.listeners.before.attach.dapui_config = function()
  dapui.open()
end
dap.listeners.before.launch.dapui_config = function()
  dapui.open()
end
dap.listeners.before.event_terminated.dapui_config = function()
  dapui.close()
end
dap.listeners.before.event_exited.dapui_config = function()
  dapui.close()
end
```
 Lastly, you can change the default way the breakpoints are displayed in the editor: init.lua 
```lua
vim.fn.sign_define('DapBreakpoint',{ text ='🟥', texthl ='', linehl ='', numhl =''})
vim.fn.sign_define('DapStopped',{ text ='▶️', texthl ='', linehl ='', numhl =''})
```
 ### Starting the dev server Since we’re not using Tauri CLI to launch the app the development server will not start automatically. To control the state of development server from Neovim you can use the [overseer](https://github.com/stevearc/overseer.nvim/tree/master) plugin. Best way to control tasks running in background is to use [VS Code style task](https://github.com/stevearc/overseer.nvim/blob/master/doc/guides.md#vs-code-tasks) configuration. To do this create a `.vscode/tasks.json` file in the projects directory. You can find example task configuration for project using `trunk` below. .vscode/tasks.json 
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "type": "process",
      "label": "dev server",
      "command": "trunk",
      "args": ["serve"],
      "isBackground": true,
      "presentation": {
        "revealProblems": "onProblem"
      },
      "problemMatcher": {
        "pattern": {
          "regexp": "^error:.*",
          "file": 1,
          "line": 2
        },
        "background": {
          "activeOnStart": false,
          "beginsPattern": ".*Rebuilding.*",
          "endsPattern": ".*server listening at:.*"
        }
      }
    }
  ]
}
```
 ### Example key bindings Below you can find example key bindings to start and control debugging sessions. init.lua 
```lua
vim.keymap.set('n', '<F5>', function() dap.continue() end)
vim.keymap.set('n', '<F6>', function() dap.disconnect({ terminateDebuggee = true }) end)
vim.keymap.set('n', '<F10>', function() dap.step_over() end)
vim.keymap.set('n', '<F11>', function() dap.step_into() end)
vim.keymap.set('n', '<F12>', function() dap.step_out() end)
vim.keymap.set('n', '<Leader>b', function() dap.toggle_breakpoint() end)
vim.keymap.set('n', '<Leader>o', function() overseer.toggle() end)
vim.keymap.set('n', '<Leader>R', function() overseer.run_template() end)
```

# Debug in JetBrains IDEs

In this guide, we’ll be setting up JetBrains RustRover for debugging the [Core Process of your Tauri app](/concept/process-model/#the-core-process). It also mostly applies to IntelliJ and CLion. ## Setting up a Cargo project Depending on which frontend stack is used in a project, the project directory may or may not be a Cargo project. By default, Tauri places the Rust project in a subdirectory called `src-tauri`. It creates a Cargo project in the root directory only if Rust is used for frontend development as well. If there’s no `Cargo.toml` file at the top level, you need to attach the project manually. Open the Cargo tool window (in the main menu, go to **View | Tool Windows | Cargo**), click **+** (**Attach Cargo Project**) on the toolbar, and select the `src-tauri/Cargo.toml` file. Alternatively, you could create a top-level Cargo workspace manually by adding the following file to the project’s root directory: Cargo.toml 
```toml
[workspace]
members = ["src-tauri"]
```
 Before you proceed, make sure that your project is fully loaded. If the Cargo tool window shows all the modules and targets of the workspace, you’re good to go. ## Setting up Run Configurations You will need to set up two separate Run/Debug configurations: * one for launching the Tauri app in debugging mode, * another one for running your frontend development server of choice. ### Tauri App 1. In the main menu, go to **Run | Edit Configurations**. 2. In the **Run/Debug Configurations** dialog: * To create a new configuration, click **+** on the toolbar and select **Cargo**. ![Add Run/Debug Configuration](/_astro/add-cargo-config-light.Bfob59bJ_1pRmgh.webp) With that created, we need to configure RustRover, so it instructs Cargo to build our app without any default features. This will tell Tauri to use your development server instead of reading assets from the disk. Normally this flag is passed by the Tauri CLI, but since we’re completely sidestepping that here, we need to pass the flag manually. ![Add --no-default-features flag](/_astro/set-no-default-features-light.CcoA2Q8U_tmggj.webp) Now we can optionally rename the Run/Debug Configuration to something more memorable, in this example we called it “Run Tauri App”, but you can name it whatever you want. ![Rename Configuration](/_astro/rename-configuration-light.B4TFjRby_Z1MQo6T.webp) ### Development Server The above configuration will use Cargo directly to build the Rust application and attach the debugger to it. This means we completely sidestep the Tauri CLI, so features like the `beforeDevCommand` and `beforeBuildCommand` will **not** be executed. We need to take care of that by running the development server manually. To create the corresponding Run configuration, you need to check the actual development server in use. Look for the `src-tauri/tauri.conf.json` file and find the following line: 
```json
    "beforeDevCommand": "pnpm dev"
```
 For `npm`, `pnpm`, or `yarn`, you could use the **npm** Run Configuration, for example: ![NPM Configuration](/_astro/npm-configuration-light.B2Rk0eaZ_Z1NO8qD.webp) Make sure you have the correct values in the **Command**, **Scripts**, and **Package Manager** fields. If your development server is `trunk` for Rust-based WebAssembly frontend frameworks, you could use the generic **Shell Script** Run Configuration: ![Trunk Serve Configuration](/_astro/trunk-configuration-light.78simsDr_1bNJJx.webp) ## Launching a Debugging Session To launch a debugging session, you first need to run your development server, and then start debugging the Tauri App by clicking the **Debug** button next to the Run Configurations Switcher. RustRover will automatically recognize breakpoints placed in any Rust file in your project and stop on the first one hit. ![Debug Session](/_astro/debug-session-light.BcVudV4z_ZIN7aw.webp) From this point, you can explore the values of your variables, step further into the code, and check what’s going at runtime in detail.

# Debug in VS Code

This guide will walk you through setting up VS Code for debugging the [Core Process of your Tauri app](/concept/process-model/#the-core-process). ## All platforms with vscode-lldb extension ### Prerequisites Install the [`vscode-lldb`](https://marketplace.visualstudio.com/items?itemName=vadimcn.vscode-lldb) extension. ### Configure launch.json Create a `.vscode/launch.json` file and paste the below JSON contents into it: .vscode/launch.json 
```json
{
  // Use IntelliSense to learn about possible attributes.
  // Hover to view descriptions of existing attributes.
  // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
  "version": "0.2.0",
  "configurations": [
    {
      "type": "lldb",
      "request": "launch",
      "name": "Tauri Development Debug",
      "cargo": {
        "args": [
          "build",
          "--manifest-path=./src-tauri/Cargo.toml",
          "--no-default-features"
        ]
      },
      // task for the `beforeDevCommand` if used, must be configured in `.vscode/tasks.json`
      "preLaunchTask": "ui:dev"
    },
    {
      "type": "lldb",
      "request": "launch",
      "name": "Tauri Production Debug",
      "cargo": {
        "args": ["build", "--release", "--manifest-path=./src-tauri/Cargo.toml"]
      },
      // task for the `beforeBuildCommand` if used, must be configured in `.vscode/tasks.json`
      "preLaunchTask": "ui:build"
    }
  ]
}
```
 This uses `cargo` directly to build the Rust application and load it in both development and production modes. Note that it does not use the Tauri CLI, so exclusive CLI features are not executed. The `beforeDevCommand` and `beforeBuildCommand` scripts must be executed beforehand or configured as a task in the `preLaunchTask` field. Below is an example `.vscode/tasks.json` file that has two tasks, one for a `beforeDevCommand` that spawns a development server and one for `beforeBuildCommand`: .vscode/tasks.json 
```json
{
  // See https://go.microsoft.com/fwlink/?LinkId=733558
  // for the documentation about the tasks.json format
  "version": "2.0.0",
  "tasks": [
    {
      "label": "ui:dev",
      "type": "shell",
      // `dev` keeps running in the background
      // ideally you should also configure a `problemMatcher`
      // see https://code.visualstudio.com/docs/editor/tasks#_can-a-background-task-be-used-as-a-prelaunchtask-in-launchjson
      "isBackground": true,
      // change this to your `beforeDevCommand`:
      "command": "yarn",
      "args": ["dev"]
    },
    {
      "label": "ui:build",
      "type": "shell",
      // change this to your `beforeBuildCommand`:
      "command": "yarn",
      "args": ["build"]
    }
  ]
}
```
 Now you can set breakpoints in `src-tauri/src/main.rs` or any other Rust file and start debugging by pressing `F5`. ## With Visual Studio Windows Debugger on Windows Visual Studio Windows Debugger is a Windows-only debugger that is generally faster than [`vscode-lldb`](https://marketplace.visualstudio.com/items?itemName=vadimcn.vscode-lldb) with better support for some Rust features such as enums. ### Prerequisites Install the [C/C++](https://marketplace.visualstudio.com/items?itemName=ms-vscode.cpptools) extension and follow <https://code.visualstudio.com/docs/cpp/config-msvc#_prerequisites> to install Visual Studio Windows Debugger. ### Configure launch.json and tasks.json .vscode/launch.json 
```json
{
  // Use IntelliSense to learn about possible attributes.
  // Hover to view descriptions of existing attributes.
  // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch App Debug",
      "type": "cppvsdbg",
      "request": "launch",
      // change the exe name to your actual exe name
      // (to debug release builds, change `target/debug` to `release/debug`)
      "program": "${workspaceRoot}/src-tauri/target/debug/your-app-name-here.exe",
      "cwd": "${workspaceRoot}",
      "preLaunchTask": "ui:dev"
    }
  ]
}
```
 Note that it does not use the Tauri CLI, so exclusive CLI features are not executed. The `tasks.json` is the same as with `lldb`, except you need to add a config group and target your `preLaunchTask` from `launch.json` to it if you want it to always compile before launching. Here is an example of running a dev server (equivalent of `beforeDevCommand`) and the compilation (`cargo build`) as a group, to use it, change the `preLaunchTask` config in `launch.json` to `dev` (or anything you named your group). .vscode/tasks.json 
```json
{
  // See https://go.microsoft.com/fwlink/?LinkId=733558
  // for the documentation about the tasks.json format
  "version": "2.0.0",
  "tasks": [
    {
      "label": "build:debug",
      "type": "cargo",
      "command": "build",
      "options": {
        "cwd": "${workspaceRoot}/src-tauri"
      }
    },
    {
      "label": "ui:dev",
      "type": "shell",
      // `dev` keeps running in the background
      // ideally you should also configure a `problemMatcher`
      // see https://code.visualstudio.com/docs/editor/tasks#_can-a-background-task-be-used-as-a-prelaunchtask-in-launchjson
      "isBackground": true,
      // change this to your `beforeDevCommand`:
      "command": "yarn",
      "args": ["dev"]
    },
    {
      "label": "dev",
      "dependsOn": ["build:debug", "ui:dev"],
      "group": {
        "kind": "build"
      }
    }
  ]
}
```

# App Icons

Tauri ships with a default iconset based on its logo. This is NOT what you want when you ship your application. To remedy this common situation, Tauri provides the `icon` command that will take an input file (`"./app-icon.png"` by default) and create all the icons needed for the various platforms. Note on filetypes * `icon.icns` = macOS * `icon.ico` = Windows * `*.png` = Linux * `Square*Logo.png` & `StoreLogo.png` = Currently unused but intended for AppX/MS Store targets. Some icon types may be used on platforms other than those listed above (especially `png`). Therefore we recommend including all icons even if you intend to only build for a subset of platforms. ## Command Usage * npm 
  ```sh
  npm run tauri icon
  ```
 * yarn 
  ```sh
  yarn tauri icon
  ```
 * pnpm 
  ```sh
  pnpm tauri icon
  ```
 * deno 
  ```sh
  deno task tauri icon
  ```
 * cargo 
  ```sh
  cargo tauri icon
  ```
 
```console
> pnpm tauri icon --help


Generate various icons for all major platforms


Usage: pnpm run tauri icon [OPTIONS] [INPUT]


Arguments:
  [INPUT]  Path to the source icon (squared PNG or SVG file with transparency) [default: ./app-icon.png]


Options:
  -o, --output <OUTPUT>        Output directory. Default: 'icons' directory next to the tauri.conf.json file
  -v, --verbose...             Enables verbose logging
  -p, --png <PNG>              Custom PNG icon sizes to generate. When set, the default icons are not generated
      --ios-color <IOS_COLOR>  The background color of the iOS icon - string as defined in the W3C's CSS Color Module Level 4 <https://www.w3.org/TR/css-color-4/> [default: #fff]
  -h, --help                   Print help
  -V, --version                Print version
```
 The **desktop** icons will be placed in your `src-tauri/icons` folder by default, where they will be included in your built app automatically. If you want to source your icons from a different location, you can edit this part of the `tauri.conf.json` file: 
```json
{
  "bundle": {
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
}
```
 The **mobile** icons will be placed into the Xcode and Android Studio projects directly! ## Creating icons manually If you prefer to build these icons yourself, for example if you want to have a simpler design for small sizes or because you don’t want to depend on the CLI’s internal image resizing, you must make sure your icons meet some requirements: * `icon.icns`: The required layer sizes and names for the [`icns`](https://en.wikipedia.org/wiki/Apple_Icon_Image_format) file are described [in the Tauri repo](https://github.com/tauri-apps/tauri/blob/1.x/tooling/cli/src/helpers/icns.json) * `icon.ico`: The [`ico`](https://en.wikipedia.org/wiki/ICO_\(file_format\)) file must include layers for 16, 24, 32, 48, 64 and 256 pixels. For an optimal display of the ICO image *in development*, the 32px layer should be the first layer. * `png`: The requirements for the png icons are: width == height, RGBA (RGB + Transparency), and 32bit per pixel (8bit per channel). Commonly expected sizes on desktop are 32, 128, 256, and 512 pixels. We recommend to at least match the output of `tauri icon`: `32x32.png`, `128x128.png`, `128x128@2x.png`, and `icon.png`. ### Android On Android you will need png icons with the same requirements but in different sizes. They will also need to be placed directly in the Android Studio project: * `src-tauri/gen/android/app/src/main/res/` * `mipmap-hdpi/` * `ic_launcher.png` & `ic_launcher_round.png`: 49x49px * `ic_launcher_foreground.png`: 162x162px * `mipmap-mdpi/` * `ic_launcher.png` & `ic_launcher_round.png`: 48x48px * `ic_launcher_foreground.png`: 108x108px * `mipmap-xhdpi/` * `ic_launcher.png` & `ic_launcher_round.png`: 96x96px * `ic_launcher_foreground.png`: 216x216px * `mipmap-xxhdpi/` * `ic_launcher.png` & `ic_launcher_round.png`: 144x144px * `ic_launcher_foreground.png`: 324x324px * `mipmap-xxxhdpi/` * `ic_launcher.png` & `ic_launcher_round.png`: 192x192px * `ic_launcher_foreground.png`: 432x432px If `tauri icon` cannot be used, we recommend checking out Android Studio’s [Image Asset Studio](https://developer.android.com/studio/write/create-app-icons) instead. ### iOS On iOS you will need png icons with the same requirements but **without transparency** and in different sizes. They will also need to be placed directly in the Xcode project into `src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/`. The following icons are expected: * 20px in 1x, 2x, 3x, with an extra icon * 29px in 1x, 2x, 3x, with an extra icon * 40px in 1x, 2x, 3x, with an extra icon * 60px in 2x, 3x * 76px in 1x, 2x * 83.5px in 2x * 512px in 2x saved as `AppIcon-512@2x.png` The file names are in the format of `AppIcon-{size}x{size}@{scaling}{extra}.png`. For the 20px icons this means you need icons in sizes 20x20, 40x40 and 60x60 named as `AppIcon-20x20@1x.png`, `AppIcon-20x20@2x.png`, `AppIcon-20x20@3x.png` and `2x` saved additionally as `AppIcon-20x20@2x-1.png` (“extra icon”).

# Plugin Development

Plugins are able to hook into the Tauri lifecycle, expose Rust code that relies on the web view APIs, handle commands with Rust, Kotlin or Swift code, and much more. Tauri offers a windowing system with web view functionality, a way to send messages between the Rust process and the web view, and an event system along with several tools to enhance the development experience. By design, the Tauri core does not contain features not needed by everyone. Instead it offers a mechanism to add external functionalities into a Tauri application called plugins. A Tauri plugin is composed of a Cargo crate and an optional NPM package that provides API bindings for its commands and events. Additionally, a plugin project can include an Android library project and a Swift package for iOS. You can learn more about developing plugins for Android and iOS in the [Mobile Plugin Development guide](/develop/plugins/develop-mobile/). ## Naming Convention Tauri plugins have a prefix followed by the plugin name. The plugin name is specified on the plugin configuration under [`tauri.conf.json > plugins`](/reference/config/#pluginconfig). By default Tauri prefixes your plugin crate with `tauri-plugin-`. This helps your plugin to be discovered by the Tauri community and to be used with the Tauri CLI. When initializing a new plugin project, you must provide its name. The generated crate name will be `tauri-plugin-{plugin-name}` and the JavaScript NPM package name will be `tauri-plugin-{plugin-name}-api` (although we recommend using an [NPM scope](https://docs.npmjs.com/about-scopes) if possible). The Tauri naming convention for NPM packages is `@scope-name/plugin-{plugin-name}`. ### Identifier Rules The `{plugin-name}` portion of a plugin crate, and any permission identifier referenced within capabilities, must follow Tauri’s identifier syntax: * Lowercase ASCII letters (`a` through `z`), digits (`0` through `9`), and hyphens (`-`). * Hyphens cannot appear as the first or last character. * A single colon (`:`) is permitted only when the identifier uses a prefix (for example `<plugin-name>:<permission-name>`). * Underscores (`_`), uppercase letters, and other characters are not allowed. * The base name is limited to 64 characters; with a prefix, the full identifier is limited to 129 characters. Examples: | Identifier | Valid? | | ------------------------- | ----------------------- | | `sqlite` | ✓ | | `sqlite-store` | ✓ | | `sqlite-store:allow-read` | ✓ | | `sqlite_store` | ✗ (underscore) | | `SqliteStore` | ✗ (uppercase) | | `-sqlite` | ✗ (leading hyphen) | | `sqlite-` | ✗ (trailing hyphen) | | `sqlite::store` | ✗ (multiple separators) | If a plugin or permission identifier violates these rules, the build fails with the error `identifiers can only include lowercase ASCII, hyphens which are not leading or trailing, and a single colon if using a prefix`. The offending value is usually the plugin name in your plugin’s `Cargo.toml` or a permission identifier in a `permissions/*.toml` file. ## Initialize Plugin Project To bootstrap a new plugin project, run `plugin new`. If you do not need the NPM package, use the `--no-api` CLI flag. If you want to initialize the plugin with Android and/or iOS support, use the `--android` and/or `--ios` flags. After installing, you can run the following to create a plugin project: * npm 
  ```sh
  npx @tauri-apps/cli plugin new [name]
  ```
 This will initialize the plugin at the directory `tauri-plugin-[name]` and, depending on the used CLI flags, the resulting project will look like this: 
```plaintext
. tauri-plugin-[name]/
├── src/                - Rust code
│ ├── commands.rs       - Defines the commands the webview can use
| ├── desktop.rs        - Desktop implementation
| ├── error.rs          - Default error type to use in returned results
│ ├── lib.rs            - Re-exports appropriate implementation, setup state...
│ ├── mobile.rs         - Mobile implementation
│ └── models.rs         - Shared structs
├── permissions/        - This will host (generated) permission files for commands
├── android             - Android library
├── ios                 - Swift package
├── guest-js            - Source code of the JavaScript API bindings
├── dist-js             - Transpiled assets from guest-js
├── Cargo.toml          - Cargo crate metadata
└── package.json        - NPM package metadata
```
 If you have an existing plugin and would like to add Android or iOS capabilities to it, you can use `plugin android add` and `plugin ios add` to bootstrap the mobile library projects and guide you through the changes needed. ## Declaring Platform Support Plugins can declare which platforms they support, and to what extent, in the `[package.metadata.platforms.support]` section of the crate’s `Cargo.toml`: Cargo.toml 
```toml
[package.metadata.platforms.support]
windows = { level = "full" }
linux = { level = "full" }
macos = { level = "full" }
android = { level = "partial", notes = "Access is restricted to the Application folder by default" }
ios = { level = "none" }
```
 Each key is a platform (`windows`, `linux`, `macos`, `android`, `ios`) and accepts two fields: * `level` (required): `"full"` if the plugin works as intended, `"partial"` if it works with limitations, or `"none"` if the platform isn’t supported. * `notes` (optional): a short description of the caveats or limitations. It renders as Markdown on the plugin’s page. In the [support table](/plugin/#support-table) it shows up as plain text in a tooltip. The support table and the platform filter on the [Features & Recipes](/plugin/) page are generated from this metadata. ## Mobile Plugin Development Plugins can run native mobile code written in Kotlin (or Java) and Swift. The default plugin template includes an Android library project using Kotlin and a Swift package. It includes an example mobile command showing how to trigger its execution from Rust code. Read more about developing plugins for mobile in the [Mobile Plugin Development guide](/develop/plugins/develop-mobile/). ## Plugin Configuration In the Tauri application where the plugin is used, the plugin configuration is specified on `tauri.conf.json` where `plugin-name` is the name of the plugin: 
```json
{
  "build": { ... },
  "tauri": { ... },
  "plugins": {
    "plugin-name": {
      "timeout": 30
    }
  }
}
```
 The plugin’s configuration is set on the `Builder` and is parsed at runtime. Here is an example of the `Config` struct being used to specify the plugin configuration: src/lib.rs 
```rust
use serde::Deserialize;
use tauri::{
    plugin::{Builder, TauriPlugin},
    Runtime,
};


// Define the plugin config
#[derive(Deserialize)]
pub struct Config {
  timeout: usize,
}


pub fn init<R: Runtime>() -> TauriPlugin<R, Config> {
  // Make the plugin config optional
  // by using `Builder::<R, Option<Config>>` instead
  Builder::<R, Config>::new("<plugin-name>")
    .setup(|app, api| {
      let timeout = api.config().timeout;
      Ok(())
    })
    .build()
}
```
 ## Lifecycle Events Plugins can hook into several lifecycle events: * [setup](#setup): Plugin is being initialized * [on_navigation](#on_navigation): Web view is attempting to perform navigation * [on_webview_ready](#on_webview_ready): New window is being created * [on_event](#on_event): Event loop events * [on_drop](#on_drop): Plugin is being deconstructed There are additional [lifecycle events for mobile plugins](/develop/plugins/develop-mobile/#lifecycle-events). ### setup * **When**: Plugin is being initialized * **Why**: Register mobile plugins, manage state, run background tasks src/lib.rs 
```rust
use tauri::{Manager, plugin::Builder};
use std::{collections::HashMap, sync::Mutex, time::Duration};


struct DummyStore(Mutex<HashMap<String, String>>);


Builder::new("<plugin-name>")
  .setup(|app, api| {
    app.manage(DummyStore(Default::default()));


    let app_ = app.clone();
    std::thread::spawn(move || {
      loop {
        app_.emit("tick", ());
        std::thread::sleep(Duration::from_secs(1));
      }
    });


    Ok(())
  })
```
 ### on_navigation * **When**: Web view is attempting to perform navigation * **Why**: Validate the navigation or track URL changes Returning `false` cancels the navigation. src/lib.rs 
```rust
use tauri::plugin::Builder;


Builder::new("<plugin-name>")
  .on_navigation(|window, url| {
    println!("window {} is navigating to {}", window.label(), url);
    // Cancels the navigation if forbidden
    url.scheme() != "forbidden"
  })
```
 ### on_webview_ready * **When**: New window has been created * **Why**: Execute an initialization script for every window src/lib.rs 
```rust
use tauri::plugin::Builder;


Builder::new("<plugin-name>")
  .on_webview_ready(|window| {
    window.listen("content-loaded", |event| {
      println!("webview content has been loaded");
    });
  })
```
 ### on_event * **When**: Event loop events * **Why**: Handle core events such as window events, menu events and application exit requested With this lifecycle hook you can be notified of any event loop [events](https://docs.rs/tauri/2.0.0/tauri/enum.RunEvent.html). src/lib.rs 
```rust
use std::{collections::HashMap, fs::write, sync::Mutex};
use tauri::{plugin::Builder, Manager, RunEvent};


struct DummyStore(Mutex<HashMap<String, String>>);


Builder::new("<plugin-name>")
  .setup(|app, _api| {
    app.manage(DummyStore(Default::default()));
    Ok(())
  })
  .on_event(|app, event| {
    match event {
      RunEvent::ExitRequested { api, .. } => {
        // user requested a window to be closed and there's no windows left


        // we can prevent the app from exiting:
        api.prevent_exit();
      }
      RunEvent::Exit => {
        // app is going to exit, you can cleanup here


        let store = app.state::<DummyStore>();
        write(
          app.path().app_local_data_dir().unwrap().join("store.json"),
          serde_json::to_string(&*store.0.lock().unwrap()).unwrap(),
        )
        .unwrap();
      }
      _ => {}
    }
  })
```
 ### on_drop * **When**: Plugin is being deconstructed * **Why**: Execute code when the plugin has been destroyed See [`Drop`](https://doc.rust-lang.org/std/ops/trait.Drop.html) for more information. src/lib.rs 
```rust
use tauri::plugin::Builder;


Builder::new("<plugin-name>")
  .on_drop(|app| {
    // plugin has been destroyed...
  })
```
 ## Exposing Rust APIs The plugin APIs defined in the project’s `desktop.rs` and `mobile.rs` are exported to the user as a struct with the same name as the plugin (in pascal case). When the plugin is setup, an instance of this struct is created and managed as a state so that users can retrieve it at any point in time with a `Manager` instance (such as `AppHandle`, `App`, or` Window`) through the extension trait defined in the plugin. For example, the [`global-shortcut plugin`](/plugin/global-shortcut/) defines a `GlobalShortcut` struct that can be read by using the `global_shortcut` method of the `GlobalShortcutExt` trait: src-tauri/src/lib.rs 
```rust
use tauri_plugin_global_shortcut::GlobalShortcutExt;


tauri::Builder::default()
  .plugin(tauri_plugin_global_shortcut::init())
  .setup(|app| {
    app.global_shortcut().register(...);
    Ok(())
  })
```
 ## Adding Commands Commands are defined in the `commands.rs` file. They are regular Tauri applications commands. They can access the AppHandle and Window instances directly, access state, and take input the same way as application commands. Read the [Commands guide](/develop/calling-rust/) for more details on Tauri commands. This command shows how to get access to the `AppHandle` and `Window` instance via dependency injection, and takes two input parameters (`on_progress` and `url`): src/commands.rs 
```rust
use tauri::{command, ipc::Channel, AppHandle, Runtime, Window};


#[command]
async fn upload<R: Runtime>(app: AppHandle<R>, window: Window<R>, on_progress: Channel, url: String) {
  // implement command logic here
  on_progress.send(100).unwrap();
}
```
 To expose the command to the webview, you must hook into the `invoke_handler()` call in `lib.rs`: src/lib.rs 
```rust
Builder::new("<plugin-name>")
    .invoke_handler(tauri::generate_handler![commands::upload])
```
 Define a binding function in `webview-src/index.ts` so that plugin users can easily call the command in JavaScript: 
```js
import { invoke, Channel } from '@tauri-apps/api/core'


export async function upload(url: string, onProgressHandler: (progress: number) => void): Promise<void> {
  const onProgress = new Channel<number>()
  onProgress.onmessage = onProgressHandler
  await invoke('plugin:<plugin-name>|upload', { url, onProgress })
}
```
 Be sure to build the TypeScript code prior to testing it. ### Command Permissions By default your commands are not accessible by the frontend. If you try to execute one of them, you will get a denied error rejection. To actually expose commands, you also need to define permissions that allow each command. #### Permission Files Permissions are defined as JSON or TOML files inside the `permissions` directory. Each file can define a list of permissions, a list of permission sets and your plugin’s default permission. ##### Permissions A permission describes privileges of your plugin commands. It can allow or deny a list of commands and associate command-specific and global scopes. permissions/start-server.toml 
```toml
"$schema" = "schemas/schema.json"


[[permission]]
identifier = "allow-start-server"
description = "Enables the start_server command."
commands.allow = ["start_server"]


[[permission]]
identifier = "deny-start-server"
description = "Denies the start_server command."
commands.deny = ["start_server"]
```
 ##### Scope Scopes allow your plugin to define deeper restrictions to individual commands. Each permission can define a list of scope objects that define something to be allowed or denied either specific to a command or globally to the plugin. Let’s define an example struct that will hold scope data for a list of binaries a `shell` plugin is allowed to spawn: src/scope.rs 
```rust
#[derive(Debug, schemars::JsonSchema)]
pub struct Entry {
    pub binary: String,
}
```
 ###### Command Scope Your plugin consumer can define a scope for a specific command in their capability file (see the [documentation](/reference/acl/scope/)). You can read the command-specific scope with the [`tauri::ipc::CommandScope`](https://docs.rs/tauri/2.0.0/tauri/ipc/struct.CommandScope.html) struct: src/commands.rs 
```rust
use tauri::ipc::CommandScope;
use crate::scope::Entry;


async fn spawn<R: tauri::Runtime>(app: tauri::AppHandle<R>, command_scope: CommandScope<'_, Entry>) -> Result<()> {
  let allowed = command_scope.allows();
  let denied = command_scope.denies();
  todo!()
}
```
 ###### Global Scope When a permission does not define any commands to be allowed or denied, it’s considered a scope permission and it should only define a global scope for your plugin: permissions/spawn-node.toml 
```toml
[[permission]]
identifier = "allow-spawn-node"
description = "This scope permits spawning the `node` binary."


[[permission.scope.allow]]
binary = "node"
```
 You can read the global scope with the [`tauri::ipc::GlobalScope`](https://docs.rs/tauri/2.0.0/tauri/ipc/struct.GlobalScope.html) struct: src/commands.rs 
```rust
use tauri::ipc::GlobalScope;
use crate::scope::Entry;


async fn spawn<R: tauri::Runtime>(app: tauri::AppHandle<R>, scope: GlobalScope<'_, Entry>) -> Result<()> {
  let allowed = scope.allows();
  let denied = scope.denies();
  todo!()
}
```
 Note We recommend checking both global and command scopes for flexibility ###### Schema The scope entry requires the `schemars` dependency to generate a JSON schema so the plugin consumers know the format of the scope and have autocomplete in their IDEs. To define the schema, first add the dependency to your Cargo.toml file: 
```toml
# we need to add schemars to both dependencies and build-dependencies because the scope.rs module is shared between the app code and build script
[dependencies]
schemars = "0.8"


[build-dependencies]
schemars = "0.8"
```
 In your build script, add the following code: build.rs 
```rust
#[path = "src/scope.rs"]
mod scope;


const COMMANDS: &[&str] = &[];


fn main() {
    tauri_plugin::Builder::new(COMMANDS)
        .global_scope_schema(schemars::schema_for!(scope::Entry))
        .build();
}
```
 ##### Permission Sets Permission sets are groups of individual permissions that helps users manage your plugin with a higher level of abstraction. For instance if a single API uses multiple commands or if there’s a logical connection between a collection of commands, you should define a set containing them: permissions/websocket.toml 
```toml
"$schema" = "schemas/schema.json"
[[set]]
identifier = "allow-websocket"
description = "Allows connecting and sending messages through a WebSocket"
permissions = ["allow-connect", "allow-send"]
```
 ##### Default Permission The default permission is a special permission set with identifier `default`. It’s recommended that you enable required commands by default. For instance the `http` plugin is useless without the `request` command allowed: permissions/default.toml 
```toml
"$schema" = "schemas/schema.json"
[default]
description = "Allows making HTTP requests"
permissions = ["allow-request"]
```
 #### Autogenerated Permissions The easiest way to define permissions for each of your commands is to use the autogeneration option defined in your plugin’s build script defined in the `build.rs` file. Inside the `COMMANDS` const, define the list of commands in snake_case (should match the command function name) and Tauri will automatically generate an `allow-$commandname` and a `deny-$commandname` permissions. The following example generates the `allow-upload` and `deny-upload` permissions: src/commands.rs 
```rust
const COMMANDS: &[&str] = &["upload"];


fn main() {
    tauri_plugin::Builder::new(COMMANDS).build();
}
```
 See the [Permissions Overview](/security/permissions/) documentation for more information. ## Managing State A plugin can manage state in the same way a Tauri application does. Read the [State Management guide](/develop/state-management/) for more information.

# Mobile Plugin Development

Plugins can run native mobile code written in Kotlin (or Java) and Swift. The default plugin template includes an Android library project using Kotlin and a Swift package including an example mobile command showing how to trigger its execution from Rust code. ## Initialize Plugin Project Follow the steps in the [Plugin Development guide](/develop/plugins/#initialize-plugin-project) to initialize a new plugin project. If you have an existing plugin and would like to add Android or iOS capabilities to it, you can use `plugin android init` and `plugin ios init` to bootstrap the mobile library projects and guide you through the changes needed. The default plugin template splits the plugin’s implementation into two separate modules: `desktop.rs` and `mobile.rs`. The desktop implementation uses Rust code to implement a functionality, while the mobile implementation sends a message to the native mobile code to execute a function and get a result back. If shared logic is needed across both implementations, it can be defined in `lib.rs`: src/lib.rs 
```rust
use tauri::Runtime;


impl<R: Runtime> <plugin-name><R> {
  pub fn do_something(&self) {
    // do something that is a shared implementation between desktop and mobile
  }
}
```
 This implementation simplifies the process of sharing an API that can be used both by commands and Rust code. ### Develop an Android Plugin A Tauri plugin for Android is defined as a Kotlin class that extends `app.tauri.plugin.Plugin` and is annotated with `app.tauri.annotation.TauriPlugin`. Each method annotated with `app.tauri.annotation.Command` can be called by Rust or JavaScript. Tauri uses Kotlin by default for the Android plugin implementation, but you can switch to Java if you prefer. After generating a plugin, right click the Kotlin plugin class in Android Studio and select the “Convert Kotlin file to Java file” option from the menu. Android Studio will guide you through the project migration to Java. ### Develop an iOS Plugin A Tauri plugin for iOS is defined as a Swift class that extends the `Plugin` class from the `Tauri` package. Each function with the `@objc` attribute and the `(_ invoke: Invoke)` parameter (for example `@objc private func download(_ invoke: Invoke) { }`) can be called by Rust or JavaScript. The plugin is defined as a [Swift package](https://www.swift.org/package-manager/) so that you can use its package manager to manage dependencies. ## Plugin Configuration Refer to the [Plugin Configuration section](/develop/plugins/#plugin-configuration) of the Plugin Development guide for more details on developing plugin configurations. The plugin instance on mobile has a getter for the plugin configuration: * Android 
  ```kotlin
  import android.app.Activity
  import android.webkit.WebView
  import app.tauri.annotation.TauriPlugin
  import app.tauri.annotation.InvokeArg


  @InvokeArg
  class Config {
      var timeout: Int? = 3000
  }


  @TauriPlugin
  class ExamplePlugin(private val activity: Activity): Plugin(activity) {
    private var timeout: Int? = 3000


    override fun load(webView: WebView) {
      getConfig(Config::class.java).let {
         this.timeout = it.timeout
      }
    }
  }
  ```
 * iOS 
  ```swift
  struct Config: Decodable {
    let timeout: Int?
  }


  class ExamplePlugin: Plugin {
    var timeout: Int? = 3000


    @objc public override func load(webview: WKWebView) {
      do {
        let config = try parseConfig(Config.self)
        self.timeout = config.timeout
      } catch {}
    }
  }
  ```
 ## Lifecycle Events Plugins can hook into several lifecycle events: * [load](#load): When the plugin is loaded into the web view * [onNewIntent](#onnewintent): Android only, when the activity is re-launched There are also the additional [lifecycle events for plugins](/develop/plugins/#lifecycle-events) in the Plugin Development guide. ### load * **When**: When the plugin is loaded into the web view * **Why**: Execute plugin initialization code - Android 
  ```kotlin
  import android.app.Activity
  import android.webkit.WebView
  import app.tauri.annotation.TauriPlugin


  @TauriPlugin
  class ExamplePlugin(private val activity: Activity): Plugin(activity) {
    override fun load(webView: WebView) {
      // perform plugin setup here
    }
  }
  ```
 - iOS 
  ```swift
  class ExamplePlugin: Plugin {
    @objc public override func load(webview: WKWebView) {
      let timeout = self.config["timeout"] as? Int ?? 30
    }
  }
  ```
 ### onNewIntent **Note**: This is only available on Android. * **When**: When the activity is re-launched. See [Activity#onNewIntent](https://developer.android.com/reference/android/app/Activity#onNewIntent\(android.content.Intent\)) for more information. * **Why**: Handle application re-launch such as when a notification is clicked or a deep link is accessed. 
```kotlin
import android.app.Activity
import android.content.Intent
import app.tauri.annotation.TauriPlugin


@TauriPlugin
class ExamplePlugin(private val activity: Activity): Plugin(activity) {
  override fun onNewIntent(intent: Intent) {
    // handle new intent event
  }
}
```
 ## Adding Mobile Commands There is a plugin class inside the respective mobile projects where commands can be defined that can be called by the Rust code: * Android 
  ```kotlin
  import android.app.Activity
  import app.tauri.annotation.Command
  import app.tauri.annotation.TauriPlugin


  @TauriPlugin
  class ExamplePlugin(private val activity: Activity): Plugin(activity) {
    @Command
    fun openCamera(invoke: Invoke) {
      val ret = JSObject()
      ret.put("path", "/path/to/photo.jpg")
      invoke.resolve(ret)
    }
  }
  ```
 If you want to use a Kotlin `suspend` function, you need to use a custom coroutine scope 
  ```kotlin
  import android.app.Activity
  import app.tauri.annotation.Command
  import app.tauri.annotation.TauriPlugin


  // Change to Dispatchers.IO if it is intended for fetching data
  val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())


  @TauriPlugin
  class ExamplePlugin(private val activity: Activity): Plugin(activity) {
    @Command
    fun openCamera(invoke: Invoke) {
      scope.launch {
        openCameraInner(invoke)
      }
    }


    private suspend fun openCameraInner(invoke: Invoke) {
      val ret = JSObject()
      ret.put("path", "/path/to/photo.jpg")
      invoke.resolve(ret)
    }
  }
  ```
 Note On Android native commands are scheduled on the main thread. Performing long-running operations will cause the UI to freeze and potentially “Application Not Responding” (ANR) error. If you need to wait for some blocking IO, you can launch a corouting like that: 
  ```kotlin
  CoroutineScope(Dispatchers.IO).launch {
    val result = myLongRunningOperation()
    invoke.resolve(result)
  }
  ```
 * iOS 
  ```swift
  class ExamplePlugin: Plugin {
    @objc public func openCamera(_ invoke: Invoke) throws {
      invoke.resolve(["path": "/path/to/photo.jpg"])
    }
  }
  ```
 Use the [`tauri::plugin::PluginHandle`](https://docs.rs/tauri/2.0.0/tauri/plugin/struct.PluginHandle.html) to call a mobile command from Rust: 
```rust
use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use tauri::Runtime;


#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CameraRequest {
  quality: usize,
  allow_edit: bool,
}


#[derive(Deserialize)]
pub struct Photo {
  path: PathBuf,
}




impl<R: Runtime> <plugin-name;pascal-case><R> {
  pub fn open_camera(&self, payload: CameraRequest) -> crate::Result<Photo> {
    self
      .0
      .run_mobile_plugin("openCamera", payload)
      .map_err(Into::into)
  }
}
```
 ## Command Arguments Arguments are serialized to commands and can be parsed on the mobile plugin with the `Invoke::parseArgs` function, taking a class describing the argument object. ### Android On Android, the arguments are defined as a class annotated with `@app.tauri.annotation.InvokeArg`. Inner objects must also be annotated: 
```kotlin
import android.app.Activity
import android.webkit.WebView
import app.tauri.annotation.Command
import app.tauri.annotation.InvokeArg
import app.tauri.annotation.TauriPlugin


@InvokeArg
internal class OpenAppArgs {
  lateinit var name: String
  var timeout: Int? = null
}


@InvokeArg
internal class OpenArgs {
  lateinit var requiredArg: String
  var allowEdit: Boolean = false
  var quality: Int = 100
  var app: OpenAppArgs? = null
}


@TauriPlugin
class ExamplePlugin(private val activity: Activity): Plugin(activity) {
  @Command
  fun openCamera(invoke: Invoke) {
    val args = invoke.parseArgs(OpenArgs::class.java)
  }
}
```
 Note Optional arguments are defined as `var <argumentName>: Type? = null` Arguments with default values are defined as `var <argumentName>: Type = <default-value>` Required arguments are defined as `lateinit var <argumentName>: Type` ### iOS On iOS, the arguments are defined as a class that inherits `Decodable`. Inner objects must also inherit the Decodable protocol: 
```swift
class OpenAppArgs: Decodable {
  let name: String
  var timeout: Int?
}


class OpenArgs: Decodable {
  let requiredArg: String
  var allowEdit: Bool?
  var quality: UInt8?
  var app: OpenAppArgs?
}


class ExamplePlugin: Plugin {
  @objc public func openCamera(_ invoke: Invoke) throws {
    let args = try invoke.parseArgs(OpenArgs.self)


    invoke.resolve(["path": "/path/to/photo.jpg"])
  }
}
```
 Note Optional arguments are defined as `var <argumentName>: Type?` Arguments with default values are **NOT** supported. Use a nullable type and set the default value on the command function instead. Required arguments are defined as `let <argumentName>: Type` ## Calling Rust From Mobile Plugins It is often preferable to write plugin code in Rust, for performance and reusability. While Tauri doesn’t directly provide a mechanism to call Rust from your plugin code, using JNI on Android and FFI on iOS allows plugins to call shared code, even when the application WebView is suspended. ### Android In your plugin’s `Cargo.toml`, add the jni crate as a dependency: 
```toml
[target.'cfg(target_os = "android")'.dependencies]
jni = "0.21"
```
 Load the application library statically and define native functions in your Kotlin code. In this example, the Kotlin class is `com.example.HelloWorld`, we need to reference the full package name from the Rust side. 
```kotlin
private const val TAG = "MyPlugin"


init {
  try {
    // Load the native library (libapp_lib.so)
    // This is the shared library built by Cargo with crate-type = ["cdylib"]
    System.loadLibrary("app_lib")
    Log.d(TAG, "Successfully loaded libapp_lib.so")
  } catch (e: UnsatisfiedLinkError) {
    Log.e(TAG, "Failed to load libapp_lib.so", e)
    throw e
  }
}


external fun helloWorld(name: String): String?
```
 Then in your plugin’s Rust code, define the function JNI will look for. The function format is `Java_package_class_method`, so for our class above this becomes `Java_com_example_HelloWorld_helloWorld` to get called by our `helloWorld` method: 
```rust
#[cfg(target_os = "android")]
#[no_mangle]
pub extern "system" fn Java_com_example_HelloWorld_helloWorld(
    mut env: JNIEnv,
    _class: JClass,
    name: JString,
) -> jstring {
    log::debug!("Calling JNI Hello World!");
    let result = format!("Hello, {}!", name);


    match env.new_string(result) {
        Ok(jstr) => jstr.into_raw(),
        Err(e) => {
            log::error!("Failed to create JString: {}", e);
            std::ptr::null_mut()
        }
    }
}
```
 ### iOS iOS only uses standard C FFI, so doesn’t need any new dependencies. Add the hook in your Swift code, as well as any necessary cleanup. These functions can be named anything valid, but must be annotated with `@_silgen_name(FFI_FUNC)`, where FFI_FUNC is a function name to be called from Rust: 
```swift
@_silgen_name("hello_world_ffi")
private static func helloWorldFFI(_ name: UnsafePointer<CChar>) -> UnsafeMutablePointer<CChar>?


@_silgen_name("free_hello_result_ffi")
private static func freeHelloResult(_ result: UnsafeMutablePointer<CChar>)


static func helloWorld(name: String) -> String? {
  // Call Rust FFI
  let resultPtr = name.withCString({ helloWorldFFI($0) })


  // Convert C string to Swift String
  let result = String(cString: resultPtr)


  // Free the C string
  freeHelloResult(resultPtr)


  return result
}
```
 Then, implement the Rust side. The `extern` functions here must match the `@_silgen_name` annotations on the Swift side: 
```rust
#[no_mangle]
pub unsafe extern "C" fn hello_world_ffi(c_name: *const c_char) -> *mut c_char {
    let name = match CStr::from_ptr(c_name).to_str() {
        Ok(s) => s,
        Err(e) => {
            log::error!("[iOS FFI] Failed to convert C string: {}", e);
            return std::ptr::null_mut();
        }
    };


    let result = format!("Hello, {}!", name);


    match CString::new(result) {
        Ok(c_str) => c_str.into_raw(),
        Err(e) => {
            log::error!("[iOS FFI] Failed to create C string: {}", e);
            std::ptr::null_mut()
        }
    }
}


#[no_mangle]
pub unsafe extern "C" fn free_hello_result_ffi(result: *mut c_char) {
    if !result.is_null() {
        drop(CString::from_raw(result));
    }
}
```
 ## Android 16KB Memory Pages Google is moving to make 16KB memory pages a requirement in all new Android app submissions. Building with an NDK version 28 or higher should automatically generate bundles that meet this requirement, but in the event an older NDK version must be used or generated files aren’t 16KB aligned, the following can be added to `.cargo/config.toml` to flag this to `rustc`: 
```toml
[target.aarch64-linux-android]
rustflags = ["-C", "link-arg=-Wl,-z,max-page-size=16384"]
```
 ## Permissions If a plugin requires permissions from the end user, Tauri simplifies the process of checking and requesting permissions. * Android First define the list of permissions needed and an alias to identify each group in code. This is done inside the `TauriPlugin` annotation: 
  ```kotlin
  @TauriPlugin(
    permissions = [
      Permission(strings = [Manifest.permission.POST_NOTIFICATIONS], alias = "postNotification")
    ]
  )
  class ExamplePlugin(private val activity: Activity): Plugin(activity) { }
  ```
 * iOS First override the `checkPermissions` and `requestPermissions` functions: 
  ```swift
  class ExamplePlugin: Plugin {
    @objc open func checkPermissions(_ invoke: Invoke) {
      invoke.resolve(["postNotification": "prompt"])
    }


    @objc public override func requestPermissions(_ invoke: Invoke) {
      // request permissions here
      // then resolve the request
      invoke.resolve(["postNotification": "granted"])
    }
  }
  ```
 Tauri automatically implements two commands for the plugin: `checkPermissions` and `requestPermissions`. Those commands can be directly called from JavaScript or Rust: * JavaScript 
  ```javascript
  import { invoke, PermissionState } from '@tauri-apps/api/core'


  interface Permissions {
    postNotification: PermissionState
  }


  // check permission state
  const permission = await invoke<Permissions>('plugin:<plugin-name>|checkPermissions')


  if (permission.postNotification === 'prompt-with-rationale') {
    // show information to the user about why permission is needed
  }


  // request permission
  if (permission.postNotification.startsWith('prompt')) {
    const state = await invoke<Permissions>('plugin:<plugin-name>|requestPermissions', { permissions: ['postNotification'] })
  }
  ```
 * Rust 
  ```rust
  use serde::{Serialize, Deserialize};
  use tauri::{plugin::PermissionState, Runtime};


  #[derive(Deserialize)]
  #[serde(rename_all = "camelCase")]
  struct PermissionResponse {
    pub post_notification: PermissionState,
  }


  #[derive(Serialize)]
  #[serde(rename_all = "camelCase")]
  struct RequestPermission {
    post_notification: bool,
  }


  impl<R: Runtime> Notification<R> {
    pub fn request_post_notification_permission(&self) -> crate::Result<PermissionState> {
      self.0
        .run_mobile_plugin::<PermissionResponse>("requestPermissions", RequestPermission { post_notification: true })
        .map(|r| r.post_notification)
        .map_err(Into::into)
    }


    pub fn check_permissions(&self) -> crate::Result<PermissionResponse> {
      self.0
        .run_mobile_plugin::<PermissionResponse>("checkPermissions", ())
        .map_err(Into::into)
    }
  }
  ```
 ## Plugin Events Plugins can emit events at any point of time using the `trigger` function: * Android 
  ```kotlin
  @TauriPlugin
  class ExamplePlugin(private val activity: Activity): Plugin(activity) {
      override fun load(webView: WebView) {
        trigger("load", JSObject())
      }


      override fun onNewIntent(intent: Intent) {
        // handle new intent event
        if (intent.action == Intent.ACTION_VIEW) {
          val data = intent.data.toString()
          val event = JSObject()
          event.put("data", data)
          trigger("newIntent", event)
        }
      }


      @Command
      fun openCamera(invoke: Invoke) {
        val payload = JSObject()
        payload.put("open", true)
        trigger("camera", payload)
      }
  }
  ```
 * iOS 
  ```swift
  class ExamplePlugin: Plugin {
    @objc public override func load(webview: WKWebView) {
      trigger("load", data: [:])
    }


    @objc public func openCamera(_ invoke: Invoke) {
      trigger("camera", data: ["open": true])
    }
  }
  ```
 The helper functions can then be called from the NPM package by using the [`addPluginListener`](/reference/javascript/api/namespacecore/#addpluginlistener) helper function: 
```javascript
import { addPluginListener, PluginListener } from '@tauri-apps/api/core';


export async function onRequest(
  handler: (url: string) => void
): Promise<PluginListener> {
  return await addPluginListener(
    '<plugin-name>',
    'event-name',
    handler
  );
}
```
 Capability Required Listening to plugin events from JavaScript is gated by the same [capability](/security/capabilities/) and [permission](/security/permissions/) system that gates plugin commands. Add the plugin’s permission (commonly `<plugin-name>:default`, or a specific `allow-listen-*` permission if the plugin defines one) to the `permissions` array of a capability under `src-tauri/capabilities/`: src-tauri/capabilities/default.json 
```json
{
  "identifier": "default",
  "windows": ["main"],
  "permissions": ["<plugin-name>:default"]
}
```
 Refer to the plugin’s own documentation for the exact permission identifiers it exposes.

# Embedding Additional Files

You may need to include additional files in your application bundle that aren’t part of your frontend (your `frontendDist`) directly or which are too big to be inlined into the binary. We call these files `resources`. ## Configuration To bundle the files of your choice, add the `resources` property to the `bundle` object in your `tauri.conf.json` file. To include a list of files: * Syntax tauri.conf.json 
  ```json
  {
    "bundle": {
      "resources": [
        "./path/to/some-file.txt",
        "/absolute/path/to/textfile.txt",
        "../relative/path/to/jsonfile.json",
        "some-folder/",
        "resources/**/*.md"
      ]
    }
  }
  ```
 * Explanation tauri.conf.json5 
  ```json
  {
    "bundle": {
      "resources": [
        // Will be placed to `$RESOURCE/path/to/some-file.txt`
        "./path/to/some-file.txt",


        // The root in an absolute path will be replaced by `_root_`,
        // so `textfile.txt` will be placed to `$RESOURCE/_root_/absolute/path/to/textfile.txt`
        "/absolute/path/to/textfile.txt",


        // `..` in a relative path will be replaced by `_up_`,
        // so `jsonfile.json` will be placed to `$RESOURCE/_up_/relative/path/to/textfile.txt`,
        "../relative/path/to/jsonfile.json",


        // If the path is a directory, the entire directory will be copied to the `$RESOURCE` directory,
        // preserving the original structures, for example:
        //   - `some-folder/file.txt`                   -> `$RESOURCE/some-folder/file.txt`
        //   - `some-folder/another-folder/config.json` -> `$RESOURCE/some-folder/another-folder/config.json`
        // This is the same as `some-folder/**/*`
        "some-folder/",


        // You can also include multiple files at once through glob patterns.
        // All the `.md` files inside `resources` will be placed to `$RESOURCE/resources/`,
        // preserving their original directory structures, for example:
        //   - `resources/index.md`      -> `$RESOURCE/resources/index.md`
        //   - `resources/docs/setup.md` -> `$RESOURCE/resources/docs/setup.md`
        "resources/**/*.md"
      ]
    }
  }
  ```
 The bundled files will be in `$RESOURCES/` with the original directory structure preserved, for example: `./path/to/some-file.txt` -> `$RESOURCE/path/to/some-file.txt` To fine control where the files will get copied to, use a map instead: * Syntax tauri.conf.json 
  ```json
  {
    "bundle": {
      "resources": {
        "/absolute/path/to/textfile.txt": "resources/textfile.txt",
        "relative/path/to/jsonfile.json": "resources/jsonfile.json",
        "resources/": "",
        "docs/**/*md": "website-docs/"
      }
    }
  }
  ```
 * Explanation tauri.conf.json5 
  ```json
  {
    "bundle": {
      "resources": {
        // `textfile.txt` will be placed to `$RESOURCE/resources/textfile.txt`
        "/absolute/path/to/textfile.txt": "resources/textfile.txt",


        // `jsonfile.json` will be placed to `$RESOURCE/resources/jsonfile.json`
        "relative/path/to/jsonfile.json": "resources/jsonfile.json",


        // Copy the entire directory to `$RESOURCE`, preserving the original structures,
        // the target is "" which means it will be placed directly in the resource directory `$RESOURCE`, for example:
        //   - `resources/file.txt`                -> `$RESOURCE/file.txt`
        //   - `resources/some-folder/config.json` -> `$RESOURCE/some-folder/config.json`
        "resources/": "",


        // When using glob patterns, the behavior is different from the list one,
        // all the matching files will be placed to the target directory without preserving the original file structures
        // for example:
        //   - `docs/index.md`         -> `$RESOURCE/website-docs/index.md`
        //   - `docs/plugins/setup.md` -> `$RESOURCE/website-docs/setup.md`
        "docs/**/*md": "website-docs/"
      }
    }
  }
  ```
 To learn about where `$RESOURCE` resolves to on each platforms, see the documentation of [`resource_dir`](https://docs.rs/tauri/latest/tauri/path/struct.PathResolver.html#method.resource_dir) ## Resolve resource file paths To resolve the path for a resource file, instead of manually calculating the path, use the following APIs * Rust On the Rust side, you need an instance of the [`PathResolver`](https://docs.rs/tauri/latest/tauri/path/struct.PathResolver.html) which you can get from [`App`](https://docs.rs/tauri/latest/tauri/struct.App.html) and [`AppHandle`](https://docs.rs/tauri/latest/tauri/struct.AppHandle.html), then call [`PathResolver::resolve`](https://docs.rs/tauri/latest/tauri/path/struct.PathResolver.html#method.resolve): 
  ```rust
  tauri::Builder::default()
    .setup(|app| {
      let resource_path = app.path().resolve("lang/de.json", BaseDirectory::Resource)?;
      Ok(())
    })
  ```
 To use it in a command: 
  ```rust
  #[tauri::command]
  fn hello(handle: tauri::AppHandle) {
    let resource_path = handle.path().resolve("lang/de.json", BaseDirectory::Resource)?;
  }
  ```
 * JavaScript To resolve the path in JavaScript, use [`resolveResource`](/reference/javascript/api/namespacepath/#resolveresource): 
  ```javascript
  import { resolveResource } from '@tauri-apps/api/path';
  const resourcePath = await resolveResource('lang/de.json');
  ```
 ### Path syntax The path in the API calls can be either a normal relative path like `folder/json_file.json` that resolves to `$RESOURCE/folder/json_file.json`, or a paths like `../relative/folder/toml_file.toml` that resolves to `$RESOURCE/_up_/relative/folder/toml_file.toml`, these APIs use the same rules as you write `tauri.conf.json > bundle > resources`, for example: tauri.conf.json 
```json
{
  "bundle": {
    "resources": ["folder/json_file.json", "../relative/folder/toml_file.toml"]
  }
}
```
 
```rust
let json_path = app.path().resolve("folder/json_file.json", BaseDirectory::Resource)?;
let toml_path = app.path().resolve("../relative/folder/toml_file.toml", BaseDirectory::Resource)?;
```
 ### Android Currently the resources are stored in the APK as assets so the return value of those APIs are not normal file system paths, we use a special URI prefix `asset://localhost/` here that can be used with the [`fs` plugin](/plugin/file-system/), with that, you can read the files through [`FsExt::fs`](https://docs.rs/tauri-plugin-fs/latest/tauri_plugin_fs/trait.FsExt.html#tymethod.fs) like this: 
```rust
let resource_path = app.path().resolve("lang/de.json", BaseDirectory::Resource).unwrap();
let json = app.fs().read_to_string(&resource_path);
```
 If you want or must have the resource files to be on a real file system, copy the contents out manually through the [`fs` plugin](/plugin/file-system/) ## Reading resource files In this example we want to bundle additional i18n json files like this: 
```plaintext
.
├── src-tauri/
│   ├── tauri.conf.json
│   ├── lang/
│   │   ├── de.json
│   │   └── en.json
│   └── ...
└── ...
```
 tauri.conf.json 
```json
{
  "bundle": {
    "resources": ["lang/*"]
  }
}
```
 lang/de.json 
```json
{
  "hello": "Guten Tag!",
  "bye": "Auf Wiedersehen!"
}
```
 ### Rust On the Rust side, you need an instance of the [`PathResolver`](https://docs.rs/tauri/latest/tauri/path/struct.PathResolver.html) which you can get from [`App`](https://docs.rs/tauri/latest/tauri/struct.App.html) and [`AppHandle`](https://docs.rs/tauri/latest/tauri/struct.AppHandle.html): 
```rust
tauri::Builder::default()
  .setup(|app| {
    // The path specified must follow the same syntax as defined in
    // `tauri.conf.json > bundle > resources`
    let resource_path = app.path().resolve("lang/de.json", BaseDirectory::Resource)?;


    let json = std::fs::read_to_string(&resource_path).unwrap();
    // Or when dealing with Android, use the file system plugin instead
    // let json = app.fs().read_to_string(&resource_path);


    let lang_de: serde_json::Value = serde_json::from_str(json).unwrap();


    // This will print 'Guten Tag!' to the terminal
    println!("{}", lang_de.get("hello").unwrap());


    Ok(())
  })
```
 
```rust
#[tauri::command]
fn hello(handle: tauri::AppHandle) -> String {
    let resource_path = handle.path().resolve("lang/de.json", BaseDirectory::Resource)?;


    let json = std::fs::read_to_string(&resource_path).unwrap();
    // Or when dealing with Android, use the file system plugin instead
    // let json = handle.fs().read_to_string(&resource_path);


    let lang_de: serde_json::Value = serde_json::from_str(json).unwrap();


    lang_de.get("hello").unwrap()
}
```
 ### JavaScript For the JavaScript side, you can either use a command like the one above and call it through `await invoke('hello')` or access the files using the [`fs` plugin](/plugin/file-system/). When using the [`fs` plugin](/plugin/file-system/), in addition to the [basic setup](/plugin/file-system/#setup), you’ll also need to configure the access control list to enable any plugin APIs you need as well as the permissions to access the `$RESOURCE` folder: src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    +"fs:allow-read-text-file",
    +"fs:allow-resource-read-recursive"
  ]
}
```
 Note Here we use `fs:allow-resource-read-recursive` to allow for full recursive read access to the complete `$RESOURCE` folder, files, and subdirectories. For more information, read [Scope Permissions](/plugin/file-system/#scopes) for other options, or [Scopes](/plugin/file-system/#scopes) for more fine-grained control. 
```javascript
import { resolveResource } from '@tauri-apps/api/path';
import { readTextFile } from '@tauri-apps/plugin-fs';


const resourcePath = await resolveResource('lang/de.json');
const langDe = JSON.parse(await readTextFile(resourcePath));
console.log(langDe.hello); // This will print 'Guten Tag!' to the devtools console
```
 ## Permissions Since we replace `../` to `_up_` in relative paths and the root to `_root_` in absolute paths when using a list, those files will be in sub folders inside the resource directory, to allow those paths in Tauri’s [permission system](/security/capabilities/), use `$RESOURCE/**/*` to allow recursive access to those files ### Examples With a file bundled like this: tauri.conf.json 
```json
{
  "bundle": {
    "resources": ["../relative/path/to/jsonfile.json"]
  }
}
```
 To use it with the [`fs` plugin](/plugin/file-system/): src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    +"fs:allow-stat",
    +"fs:allow-read-text-file",
    +"fs:allow-resource-read-recursive",
+    {
      +"identifier": "fs:scope",
      +"allow": ["$RESOURCE/**/*"],
      +"deny": ["$RESOURCE/secret.txt"]
+    }
  ]
}
```
 To use it with the [`opener` plugin](/plugin/opener/): src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
+    {
      +"identifier": "opener:allow-open-path",
      +"allow": [
+        {
          +"path": "$RESOURCE/**/*"
+        }
+      ]
+    }
  ]
}
```

# Embedding External Binaries

You may need to embed external binaries to add additional functionality to your application or prevent users from installing additional dependencies (e.g., Node.js or Python). We call this binary a `sidecar`. Binaries are executables written in any programming language. Common use cases are Python CLI applications or API servers bundled using `pyinstaller`. To bundle the binaries of your choice, you can add the `externalBin` property to the `bundle` object in your `tauri.conf.json`. The `externalBin` configuration expects a list of strings targeting binaries either with absolute or relative paths. Here is a Tauri configuration snippet to illustrate a sidecar configuration: src-tauri/tauri.conf.json 
```json
{
  "bundle": {
    "externalBin": [
      "/absolute/path/to/sidecar",
      "../relative/path/to/binary",
      "binaries/my-sidecar"
    ]
  }
}
```
 Note The relative paths are relative to the `tauri.conf.json` file which is in the `src-tauri` directory. So `binaries/my-sidecar` would represent `<PROJECT ROOT>/src-tauri/binaries/my-sidecar`. To make the external binary work on each supported architecture, a binary with the same name and a `-$TARGET_TRIPLE` suffix must exist on the specified path. For instance, `"externalBin": ["binaries/my-sidecar"]` requires a `src-tauri/binaries/my-sidecar-x86_64-unknown-linux-gnu` executable on Linux or `src-tauri/binaries/my-sidecar-aarch64-apple-darwin` on Mac OS with Apple Silicon. You can find your **current** platform’s `-$TARGET_TRIPLE` suffix by running the following command: 
```sh
rustc --print host-tuple
```
 This directly outputs your host’s target triple (e.g., `x86_64-unknown-linux-gnu` or `aarch64-apple-darwin`). Note The `--print host-tuple` flag was added in Rust 1.84.0. If you’re using an older version, you’ll need to parse the output of `rustc -Vv` instead: 
```sh
# Unix (Linux/macOS)
rustc -Vv | grep host | cut -f2 -d' '


# Windows PowerShell
rustc -Vv | Select-String "host:" | ForEach-Object {$_.Line.split(" ")[1]}
```
 Here’s a Node.js script to append the target triple to a binary: 
```javascript
import { execSync } from 'child_process';
import fs from 'fs';


const extension = process.platform === 'win32' ? '.exe' : '';


const targetTriple = execSync('rustc --print host-tuple').toString().trim();
if (!targetTriple) {
  console.error('Failed to determine platform target triple');
}
fs.renameSync(
  `src-tauri/binaries/sidecar${extension}`,
  `src-tauri/binaries/sidecar-${targetTriple}${extension}`
);
```
 Note that this script will not work if you compile for a different architecture than the one its running on, so only use it as a starting point for your own build scripts. ## Running it from Rust Note Please follow the [shell plugin guide](/plugin/shell/) first to set up and initialize the plugin correctly. Without the plugin being initialized and configured the example won’t work. On the Rust side, import the `tauri_plugin_shell::ShellExt` trait and call the `shell().sidecar()` function on the AppHandle: 
```rust
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;
use tauri::Emitter;


let sidecar_command = app.shell().sidecar("my-sidecar").unwrap();
let (mut rx, mut child) = sidecar_command
  .spawn()
  .expect("Failed to spawn sidecar");


tauri::async_runtime::spawn(async move {
  // read events such as stdout
  while let Some(event) = rx.recv().await {
    if let CommandEvent::Stdout(line_bytes) = event {
      let line = String::from_utf8_lossy(&line_bytes);
      app
        .emit("message", Some(format!("'{}'", line)))
        .expect("failed to emit event");
      // write to stdin
      child.write("message from Rust\n".as_bytes()).unwrap();
    }
  }
});
```
 Note The `sidecar()` function expects just the filename, NOT the whole path configured in the `externalBin` array. Given the following configuration: src-tauri/tauri.conf.json 
```json
{
  "bundle": {
    "externalBin": ["binaries/app", "my-sidecar", "../scripts/sidecar"]
  }
}
```
 The appropriate way to execute the sidecar is by calling `app.shell().sidecar(name)` where `name` is either `"app"`, `"my-sidecar"` or `"sidecar"` instead of `"binaries/app"` for instance. You can place this code inside a Tauri command to easily pass the AppHandle or you can store a reference to the AppHandle in the builder script to access it elsewhere in your application. ## Running it from JavaScript When running the sidecar, Tauri requires you to give the sidecar permission to run the `execute` or `spawn` method on the child process. To grant this permission, go to the file `<PROJECT ROOT>/src-tauri/capabilities/default.json` and add the section below to the permissions array. Don’t forget to name your sidecar according to the relative path mentioned earlier. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    "core:default",
+    {
      +"identifier": "shell:allow-execute",
      +"allow": [
+        {
          +"name": "binaries/app",
          +"sidecar": true
+        }
+      ]
+    }
  ]
}
```
 Note The `shell:allow-execute` identifier is used because the sidecar’s child process will be started using the `command.execute()` method. To run it with `command.spawn()`, you need to change the identifier to `shell:allow-spawn` or add another entry to the array with the same structure as the one above, but with the identifier set to `shell:allow-spawn`. In the JavaScript code, import the `Command` class from the `@tauri-apps/plugin-shell` module and use the `sidecar` static method. 
```javascript
import { Command } from '@tauri-apps/plugin-shell';
const command = Command.sidecar('binaries/my-sidecar');
const output = await command.execute();
```
 Note The string provided to `Command.sidecar` must match one of the strings defined in the `externalBin` configuration array. ## Passing arguments You can pass arguments to Sidecar commands just like you would for running normal [Command](https://doc.rust-lang.org/std/process/struct.Command.html). Arguments can be either **static** (e.g. `-o` or `serve`) or **dynamic** (e.g. `<file_path>` or `localhost:<PORT>`). A value of `true` will allow any arguments to be passed to the command. `false` will disable all arguments. If neither `true` or `false` is set, you define the arguments in the exact order in which you’d call them. Static arguments are defined as-is, while dynamic arguments can be defined using a regular expression. First, define the arguments that need to be passed to the sidecar command in `src-tauri/capabilities/default.json`: src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
+    {
      +"identifier": "shell:allow-execute",
      +"allow": [
+        {
          +"args": [
            +"arg1",
            +"-a",
            +"--arg2",
+            {
              +"validator": "\\S+"
+            }
+          ],
          +"name": "binaries/my-sidecar",
          +"sidecar": true
+        }
+      ]
+    }
  ]
}
```
 Note If you are migrating from Tauri v1, the `migrate` command in Tauri v2 CLI should take care of this for you. Read [Automated Migration](/start/migrate/from-tauri-1/#automated-migration) for more. Then, to call the sidecar command, simply pass in **all** the arguments as an array. In Rust: 
```rust
use tauri_plugin_shell::ShellExt;
#[tauri::command]
async fn call_my_sidecar(app: tauri::AppHandle) {
  let sidecar_command = app
    .shell()
    .sidecar("my-sidecar")
    .unwrap()
    .args(["arg1", "-a", "--arg2", "any-string-that-matches-the-validator"]);
  let (mut _rx, mut _child) = sidecar_command.spawn().unwrap();
}
```
 In JavaScript: 
```javascript
import { Command } from '@tauri-apps/plugin-shell';
// notice that the args array matches EXACTLY what is specified in `capabilities/default.json`.
const command = Command.sidecar('binaries/my-sidecar', [
  'arg1',
  '-a',
  '--arg2',
  'any-string-that-matches-the-validator',
]);
const output = await command.execute();
```

# State Management

In a Tauri application, you often need to keep track of the current state of your application or manage the lifecycle of things associated with it. Tauri provides an easy way to manage the state of your application using the [`Manager`](https://docs.rs/tauri/latest/tauri/trait.Manager.html) API, and read it when commands are called. Here is a simple example: 
```rust
use tauri::{Builder, Manager};


struct AppData {
  welcome_message: &'static str,
}


fn main() {
  Builder::default()
    .setup(|app| {
      app.manage(AppData {
        welcome_message: "Welcome to Tauri!",
      });
      Ok(())
    })
    .run(tauri::generate_context!())
    .unwrap();
}
```
 You can later access your state with any type that implements the [`Manager`](https://docs.rs/tauri/latest/tauri/trait.Manager.html) trait, for example the [`App`](https://docs.rs/tauri/latest/tauri/struct.App.html) instance: 
```rust
let data = app.state::<AppData>();
```
 For more info, including accessing state in commands, see the [Accessing State](#accessing-state) section. ## Mutability In Rust, you cannot directly mutate values which are shared between multiple threads or when ownership is controlled through a shared pointer such as [`Arc`](https://doc.rust-lang.org/stable/std/sync/struct.Arc.html) (or Tauri’s [`State`](https://docs.rs/tauri/latest/tauri/struct.State.html)). Doing so could cause data races (for example, two writes happening simultaneously). To work around this, you can use a concept known as [interior mutability](https://doc.rust-lang.org/book/ch15-05-interior-mutability.html). For example, the standard library’s [`Mutex`](https://doc.rust-lang.org/stable/std/sync/struct.Mutex.html) can be used to wrap your state. This allows you to lock the value when you need to modify it, and unlock it when you are done. 
```rust
use std::sync::Mutex;


use tauri::{Builder, Manager};


#[derive(Default)]
struct AppState {
  counter: u32,
}


fn main() {
  Builder::default()
    .setup(|app| {
      app.manage(Mutex::new(AppState::default()));
      Ok(())
    })
    .run(tauri::generate_context!())
    .unwrap();
}
```
 The state can now be modified by locking the mutex: 
```rust
let state = app.state::<Mutex<AppState>>();


// Lock the mutex to get mutable access:
let mut state = state.lock().unwrap();


// Modify the state:
state.counter += 1;
```
 At the end of the scope, or when the `MutexGuard` is otherwise dropped, the mutex is unlocked automatically so that other parts of your application can access and mutate the data within. ### When to use an async mutex To quote the [Tokio documentation](https://docs.rs/tokio/latest/tokio/sync/struct.Mutex.html#which-kind-of-mutex-should-you-use), it’s often fine to use the standard library’s [`Mutex`](https://doc.rust-lang.org/stable/std/sync/struct.Mutex.html) instead of an async mutex such as the one Tokio provides: > Contrary to popular belief, it is ok and often preferred to use the ordinary Mutex from the standard library in asynchronous code … The primary use case for the async mutex is to provide shared mutable access to IO resources such as a database connection. It’s a good idea to read the linked documentation fully to understand the trade-offs between the two. One reason you *would* need an async mutex is if you need to hold the `MutexGuard` across await points. ### Do you need `Arc`? It’s common to see [`Arc`](https://doc.rust-lang.org/stable/std/sync/struct.Arc.html) used in Rust to share ownership of a value across multiple threads (usually paired with a [`Mutex`](https://doc.rust-lang.org/stable/std/sync/struct.Mutex.html) in the form of `Arc<Mutex<T>>`). However, you don’t need to use [`Arc`](https://doc.rust-lang.org/stable/std/sync/struct.Arc.html) for things stored in [`State`](https://docs.rs/tauri/latest/tauri/struct.State.html) because Tauri will do this for you. In case `State`’s lifetime requirements prevent you from moving your state into a new thread you can instead move an `AppHandle` into the thread and then retrieve your state as shown below in the “[Access state with the Manager trait](#access-state-with-the-manager-trait)” section. `AppHandle`s are deliberately cheap to clone for use-cases like this. ## Accessing State ### Access state in commands 
```rust
#[tauri::command]
fn increase_counter(state: State<'_, Mutex<AppState>>) -> u32 {
  let mut state = state.lock().unwrap();
  state.counter += 1;
  state.counter
}
```
 For more information on commands, see [Calling Rust from the Frontend](/develop/calling-rust/). #### Async commands If you are using `async` commands and want to use Tokio’s async [`Mutex`](https://docs.rs/tokio/latest/tokio/sync/struct.Mutex.html), you can set it up the same way and access the state like this: 
```rust
#[tauri::command]
async fn increase_counter(state: State<'_, Mutex<AppState>>) -> Result<u32, ()> {
  let mut state = state.lock().await;
  state.counter += 1;
  Ok(state.counter)
}
```
 Note that the return type must be [`Result`](https://doc.rust-lang.org/stable/std/result/index.html) here because this async command takes a borrowed argument (`State<'_, T>`). Async commands with only owned arguments can return a value directly. See [Async Commands](/develop/calling-rust/#async-commands) for details. ### Access state with the [`Manager`](https://docs.rs/tauri/latest/tauri/trait.Manager.html) trait Sometimes you may need to access the state outside of commands, such as in a different thread or in an event handler like `on_window_event`. In such cases, you can use the `state()` method of types that implement the [`Manager`](https://docs.rs/tauri/latest/tauri/trait.Manager.html) trait (such as the `AppHandle`) to get the state: 
```rust
use std::sync::Mutex;
use tauri::{Builder, Window, WindowEvent, Manager};


#[derive(Default)]
struct AppState {
  counter: u32,
}


// In an event handler:
fn on_window_event(window: &Window, _event: &WindowEvent) {
    // Get a handle to the app so we can get the global state.
    let app_handle = window.app_handle();
    let state = app_handle.state::<Mutex<AppState>>();


    // Lock the mutex to mutably access the state.
    let mut state = state.lock().unwrap();
    state.counter += 1;
}


fn main() {
  Builder::default()
    .setup(|app| {
      app.manage(Mutex::new(AppState::default()));
      Ok(())
    })
    .on_window_event(on_window_event)
    .run(tauri::generate_context!())
    .unwrap();
}
```
 This method is useful when you cannot rely on command injection. For example, if you need to move the state into a thread where using an `AppHandle` is easier, or if you are not in a command context. ## Mismatching Types Caution If you use the wrong type for the [`State`](https://docs.rs/tauri/latest/tauri/struct.State.html) parameter, you will not get a compile time error. Instead, invoking the command fails at runtime: the `invoke` call on the frontend is rejected with a `state not managed for field ...` error. Retrieving an unmanaged type directly with `Manager::state()` panics instead. For example, if you use `State<'_, AppState>` instead of `State<'_, Mutex<AppState>>`, there won’t be any state managed with that type. If you prefer, you can wrap your state with a type alias to prevent this mistake: 
```rust
use std::sync::Mutex;


#[derive(Default)]
struct AppStateInner {
  counter: u32,
}


type AppState = Mutex<AppStateInner>;
```
 However, make sure to use the type alias as it is, and not wrap it in a [`Mutex`](https://doc.rust-lang.org/stable/std/sync/struct.Mutex.html) a second time, otherwise you will run into the same issue.

# Tests

> Techniques for testing inside and outside the Tauri runtime

Tauri offers support for both unit and integration testing utilizing a mock runtime. Under the mock runtime, native webview libraries are not executed. [See more about the mock runtime here](/develop/tests/mocking/). Tauri also provides support for end-to-end testing utilizing the WebDriver protocol. [WebdriverIO Tauri testing](https://webdriver.io/docs/desktop-testing/tauri) supports Windows, Linux, and macOS; the WebDriver protocol can also be driven directly on Windows and Linux, as macOS provides no desktop WebDriver client. [See more about WebDriver support here](/develop/tests/webdriver/). We offer [tauri-action](https://github.com/tauri-apps/tauri-action) to help run GitHub actions, but any sort of CI/CD runner can be used with Tauri as long as each platform has the required libraries installed to compile against.

# Mock Tauri APIs

When writing your frontend tests, having a “fake” Tauri environment to simulate windows or intercept IPC calls is common, so-called *mocking*. The [`@tauri-apps/api/mocks`](/reference/javascript/api/namespacemocks/) module provides some helpful tools to make this easier for you: Caution Remember to clear mocks after each test run to undo mock state changes between runs! See [`clearMocks()`](/reference/javascript/api/namespacemocks/#clearmocks) docs for more info. ## IPC Requests Most commonly, you want to intercept IPC requests; this can be helpful in a variety of situations: * Ensure the correct backend calls are made * Simulate different results from backend functions Tauri provides the mockIPC function to intercept IPC requests. You can find more about the specific API in detail [here](/reference/javascript/api/namespacemocks/#mockipc). Note The following examples use [Vitest](https://vitest.dev), but you can use any other frontend testing library such as jest. ### Mocking Commands for `invoke` 
```javascript
import { beforeAll, expect, test } from "vitest";
import { randomFillSync } from "crypto";


import { mockIPC } from "@tauri-apps/api/mocks";
import { invoke } from "@tauri-apps/api/core";


// jsdom doesn't come with a WebCrypto implementation
beforeAll(() => {
  Object.defineProperty(window, 'crypto', {
    value: {
      // @ts-ignore
      getRandomValues: (buffer) => {
        return randomFillSync(buffer);
      },
    },
  });
});




test("invoke simple", async () => {
  mockIPC((cmd, args) => {
    // simulated rust command called "add" that just adds two numbers
    if(cmd === "add") {
      return (args.a as number) + (args.b as number);
    }
  });
});
```
 Sometimes you want to track more information about an IPC call; how many times was the command invoked? Was it invoked at all? You can use [`mockIPC()`](/reference/javascript/api/namespacemocks/#mockipc) with other spying and mocking tools to test this: 
```javascript
import { beforeAll, expect, test, vi } from "vitest";
import { randomFillSync } from "crypto";


import { mockIPC } from "@tauri-apps/api/mocks";
import { invoke } from "@tauri-apps/api/core";


// jsdom doesn't come with a WebCrypto implementation
beforeAll(() => {
  Object.defineProperty(window, 'crypto', {
    value: {
      // @ts-ignore
      getRandomValues: (buffer) => {
        return randomFillSync(buffer);
      },
    },
  });
});




test("invoke", async () => {
  mockIPC((cmd, args) => {
    // simulated rust command called "add" that just adds two numbers
    if(cmd === "add") {
      return (args.a as number) + (args.b as number);
    }
  });


  // we can use the spying tools provided by vitest to track the mocked function
  const spy = vi.spyOn(window.__TAURI_INTERNALS__, "invoke");


  expect(invoke("add", { a: 12, b: 15 })).resolves.toBe(27);
  expect(spy).toHaveBeenCalled();
});
```
 To mock IPC requests to a sidecar or shell command you need to grab the ID of the event handler when `spawn()` or `execute()` is called and use this ID to emit events the backend would send back: 
```javascript
mockIPC(async (cmd, args) => {
  if (args.message.cmd === 'execute') {
    const eventCallbackId = `_${args.message.onEventFn}`;
    const eventEmitter = window[eventCallbackId];


    // 'Stdout' event can be called multiple times
    eventEmitter({
      event: 'Stdout',
      payload: 'some data sent from the process',
    });


    // 'Terminated' event must be called at the end to resolve the promise
    eventEmitter({
      event: 'Terminated',
      payload: {
        code: 0,
        signal: 'kill',
      },
    });
  }
});
```
 See also `mockIPC` fakes `invoke` under the mock runtime — no real webview or Rust backend runs. To mock the same commands in **end-to-end** tests, against a running app or your frontend in a browser, [`@wdio/tauri-service`](https://webdriver.io/docs/desktop-testing/tauri) provides an equivalent `browser.tauri.mock()`. See [WebDriver testing](/develop/tests/webdriver/). ### Mocking Events [Since `2.7.0`](https://v2.tauri.app/release/tauri/v2.7.0/) There is partial support of the [Event System](/develop/calling-frontend/#event-system) to simulate events emitted by your Rust code via the `shouldMockEvents` option: 
```javascript
import { mockIPC, clearMocks } from '@tauri-apps/api/mocks';
import { emit, listen } from '@tauri-apps/api/event';
import { afterEach, expect, test, vi } from 'vitest';


test('mocked event', () => {
  mockIPC(() => {}, { shouldMockEvents: true }); // enable event mocking


  const eventHandler = vi.fn();
  listen('test-event', eventHandler);


  emit('test-event', { foo: 'bar' });
  expect(eventHandler).toHaveBeenCalledWith({
    event: 'test-event',
    payload: { foo: 'bar' },
  });
});
```
 `emitTo` and `emit_filter` are **not** supported yet. ## Windows Sometimes you have window-specific code (a splash screen window, for example), so you need to simulate different windows. You can use the [`mockWindows()`](/reference/javascript/api/namespacemocks/#mockwindows) method to create fake window labels. The first string identifies the “current” window (i.e., the window your JavaScript believes itself in), and all other strings are treated as additional windows. Note [`mockWindows()`](/reference/javascript/api/namespacemocks/#mockwindows) only fakes the existence of windows but no window properties. To simulate window properties, you need to intercept the correct calls using [`mockIPC()`](/reference/javascript/api/namespacemocks/#mockipc) 
```javascript
import { beforeAll, expect, test } from 'vitest';
import { randomFillSync } from 'crypto';


import { mockWindows } from '@tauri-apps/api/mocks';


// jsdom doesn't come with a WebCrypto implementation
beforeAll(() => {
  Object.defineProperty(window, 'crypto', {
    value: {
      // @ts-ignore
      getRandomValues: (buffer) => {
        return randomFillSync(buffer);
      },
    },
  });
});


test('invoke', async () => {
  mockWindows('main', 'second', 'third');


  const { getCurrent, getAll } = await import('@tauri-apps/api/webviewWindow');


  expect(getCurrent()).toHaveProperty('label', 'main');
  expect(getAll().map((w) => w.label)).toEqual(['main', 'second', 'third']);
});
```

# WebDriver

> WebDriver Testing

[WebDriver](https://www.w3.org/TR/webdriver/) is a standardized interface to interact with web documents, primarily intended for automated testing. The recommended way to use it with Tauri is [WebdriverIO](https://webdriver.io/) and the [`@wdio/tauri-service`](https://webdriver.io/docs/desktop-testing/tauri), which works on **Windows, Linux, and macOS**. Maintained under the WebdriverIO project, it provides Tauri API access through `browser.tauri.execute()`, command (IPC) mocking, frontend and backend log capture, and multiremote. By default the service runs an **embedded WebDriver server** inside your app, so no external driver is needed on any platform — and this is how macOS is supported. It can also drive the platform’s native WebDriver through [`tauri-driver`](https://crates.io/crates/tauri-driver) on Windows and Linux, or [CrabNebula](https://crabnebula.dev)’s cross-platform fork of `tauri-driver` on all platforms (a paid API key is required for macOS). Whichever route you choose, the service detects your application binary, and on the `tauri-driver` route it keeps the Edge WebDriver in sync on Windows for you. The quickest way to scaffold a project is the WebdriverIO starter: 
```shell
npm create wdio@latest ./
```
 Pick **Desktop Testing** and choose **Tauri** at the framework prompt. A minimal configuration looks like this: 
```typescript
export const config: WebdriverIO.Config = {
  services: [
    [
      'tauri',
      {
        appBinaryPath: './src-tauri/target/release/my-tauri-app',
        driverProvider: 'embedded',
      },
    ],
  ],
};
```
 Setting this up uses two small Tauri plugins, both optional depending on your requirements: * **`tauri-plugin-wdio-webdriver`** runs the embedded WebDriver server. It’s required for the `embedded` provider (the default) — the service drives your app through it, with no external driver, and it’s how macOS is supported. You can skip it if you want to use the `external` or `crabnebula` provider instead. * **`tauri-plugin-wdio`** enables backend access including: `browser.tauri.execute()`, command (IPC) mocking, and log capture. See [Plugin Setup](https://webdriver.io/docs/desktop-testing/tauri/plugin-setup) for the full steps, and the [CrabNebula setup guide](https://webdriver.io/docs/desktop-testing/tauri/crabnebula-setup) if you use that provider. For fast, renderer-only tests there is also a **browser mode** that runs your Tauri frontend in plain Chrome against a Vite dev server — no Tauri binary, driver, or plugin required. It intercepts `invoke()` calls so you can mock commands and assert on their arguments with the same WDIO API. See the [browser mode guide](https://github.com/webdriverio/desktop-mobile/blob/main/packages/tauri-service/docs/browser-mode.md). [WebdriverIO Tauri documentation](https://webdriver.io/docs/desktop-testing/tauri)Full setup, configuration, and API reference for @wdio/tauri-service ## Example Applications Complete, runnable examples that use the service live in the [WebdriverIO desktop-mobile repository](https://github.com/webdriverio/desktop-mobile/tree/main/fixtures/e2e-apps/tauri). ## Continuous Integration (CI) The WebDriver CI guide explains how to run these tests under GitHub Actions and the concepts behind it. [Continuous Integration (CI)](/develop/tests/webdriver/ci/) ## Driving `tauri-driver` directly If you are not using Node.js, prefer [Selenium](/develop/tests/webdriver/example/selenium/), or are integrating WebDriver into a custom test harness, you can drive [`tauri-driver`](https://crates.io/crates/tauri-driver) directly instead of using the service. Driven directly, only Windows and Linux are supported on desktop, as macOS has no WKWebView driver tool available (use the service’s embedded WebDriver server for macOS). [Manual WebDriver setup](/develop/tests/webdriver/manual-setup/)Install and drive tauri-driver yourself (Windows and Linux only)

# Continuous Integration

> WebDriver Testing

It is possible to run [WebDriver](https://www.w3.org/TR/webdriver/) tests with [`tauri-driver`](https://crates.io/crates/tauri-driver) on your CI. The following example uses the [WebdriverIO](https://webdriver.io/) example we [previously built together](/develop/tests/webdriver/example/webdriverio/) and GitHub Actions. The WebDriver tests are executed on Linux by creating a fake display. Some CI systems such as GitHub Actions also support running WebDriver tests on Windows. ## GitHub Actions The following GitHub Actions assumes: 1. The Tauri application is in the `src-tauri` folder. 2. The [WebDriverIO](https://webdriver.io/) test runner is in the `e2e-tests` directory and runs when `yarn test` is used in that directory. .github/workflows/webdriver.yml 
```yaml
# run this action when the repository is pushed to
on: [push]


# the name of our workflow
name: WebDriver


jobs:
  # a single job named test
  test:
    # the display name of the test job
    name: WebDriverIO Test Runner


    # run on the matrix platform
    runs-on: ${{ matrix.platform }}
    strategy:
      # do not fail other matrix runs if one fails
      fail-fast: false
      # set all platforms our test should run on
      matrix:
        platform: [ubuntu-latest, windows-latest]


    # the steps our job runs **in order**
    steps:
      # checkout the code on the workflow runner
      - uses: actions/checkout@v4


      # install system dependencies that Tauri needs to compile on Linux.
      # note the extra dependencies for `tauri-driver` to run which are: `webkit2gtk-driver` and `xvfb`
      - name: Tauri dependencies
        if: matrix.platform == 'ubuntu-latest'
        run: |
          sudo apt-get update &&
          sudo apt-get install -y \
          libwebkit2gtk-4.1-dev \
          libayatana-appindicator3-dev \
          webkit2gtk-driver \
          xvfb


      # install a matching Microsoft Edge Driver version using msedgedriver-tool
      - name: install msdgedriver (Windows)
        if: matrix.platform == 'windows-latest'
        run: |
          cargo install --git https://github.com/chippers/msedgedriver-tool
          & "$HOME/.cargo/bin/msedgedriver-tool.exe"
          $PWD.Path >> $env:GITHUB_PATH


      # install latest stable Rust release
      - name: Setup rust-toolchain stable
        uses: dtolnay/rust-toolchain@stable


      # setup caching for the Rust target folder
      - name: Setup Rust cache
        uses: Swatinem/rust-cache@v2
        with:
          workspaces: src-tauri


      # we run our Rust tests before the webdriver tests to avoid testing a broken application
      - name: Cargo test
        run: cargo test


      # install the latest stable node version at the time of writing
      - name: Node 24
        uses: actions/setup-node@v4
        with:
          node-version: 24
          cache: 'yarn'


      # install the application Node.js dependencies with Yarn
      - name: Yarn install
        run: yarn install --frozen-lockfile


      # install the e2e-tests Node.js dependencies with Yarn
      - name: Yarn install
        run: yarn install --frozen-lockfile
        working-directory: e2e-tests


      # install the latest version of `tauri-driver`.
      # note: the tauri-driver version is independent of any other Tauri versions
      - name: Install tauri-driver
        run: cargo install tauri-driver --locked


      # run the WebdriverIO test suite on Linux.
      # we run it through `xvfb-run` (the dependency we installed earlier) to have a fake
      # display server which allows our application to run headless without any changes to the code
      - name: WebdriverIO (Linux)
        if: matrix.platform == 'ubuntu-latest'
        run: xvfb-run yarn test
        working-directory: e2e-tests


      # run the WebdriverIO test suite on Windows.
      # in this case we can run the tests directly.
      - name: WebdriverIO (Windows)
        if: matrix.platform == 'windows-latest'
        run: yarn test
        working-directory: e2e-tests
```

# Selenium

Note Make sure to go through the [prerequisites instructions](/develop/tests/webdriver/manual-setup/) to be able to follow this guide. This WebDriver testing example will use [Selenium](https://selenium.dev/) and a popular Node.js testing suite. You are expected to already have Node.js installed, along with `npm` or `yarn` although the [finished example project](https://github.com/tauri-apps/webdriver-example) uses `pnpm`. ## Create a Directory for the Tests Let’s create a space to write these tests in our project. We will be using a nested directory for this example project as we will later also go over other frameworks, but typically you will only need to use one. Create the directory we will use with `mkdir -p e2e-tests`. The rest of this guide will assume you are inside the `e2e-tests` directory. ## Initializing a Selenium Project We will be using a pre-existing `package.json` to bootstrap this test suite because we have already chosen specific dependencies to use and want to showcase a simple working solution. The bottom of this section has a collapsed guide on how to set it up from scratch. `package.json`: 
```json
{
  "name": "selenium",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "mocha"
  },
  "dependencies": {
    "chai": "^5.2.1",
    "mocha": "^11.7.1",
    "selenium-webdriver": "^4.34.0"
  }
}
```
 We have a script that runs [Mocha](https://mochajs.org/) as a test framework exposed as the `test` command. We also have various dependencies that we will be using to run the tests. [Mocha](https://mochajs.org/) as the testing framework, [Chai](https://www.chaijs.com/) as the assertion library, and [`selenium-webdriver`](https://www.npmx.dev/package/selenium-webdriver) which is the Node.js [Selenium](https://selenium.dev/) package. ## Testing Unlike the [WebdriverIO Test Suite](/develop/tests/webdriver/example/webdriverio/#config), Selenium does not come out of the box with a Test Suite and leaves it up to the developer to build those out. We chose [Mocha](https://mochajs.org/), which is pretty neutral and not related to WebDrivers, so our script will need to do a bit of work to set up everything for us in the correct order. [Mocha](https://mochajs.org/) expects a testing file at `test/test.js` by default, so let’s create that file now. `test/test.js`: 
```javascript
import os from 'os';
import path from 'path';
import { expect } from 'chai';
import { spawn, spawnSync } from 'child_process';
import { Builder, By, Capabilities } from 'selenium-webdriver';
import { fileURLToPath } from 'url';


const __dirname = fileURLToPath(new URL('.', import.meta.url));


// create the path to the expected application binary
const application = path.resolve(
  __dirname,
  '..',
  '..',
  'src-tauri',
  'target',
  'debug',
  'tauri-app'
);


// keep track of the webdriver instance we create
let driver;


// keep track of the tauri-driver process we start
let tauriDriver;
let exit = false;


before(async function () {
  // set timeout to 2 minutes to allow the program to build if it needs to
  this.timeout(120000);


  // ensure the app has been built
  spawnSync('yarn', ['tauri', 'build', '--debug', '--no-bundle'], {
    cwd: path.resolve(__dirname, '../..'),
    stdio: 'inherit',
    shell: true,
  });


  // start tauri-driver
  tauriDriver = spawn(
    path.resolve(os.homedir(), '.cargo', 'bin', 'tauri-driver'),
    [],
    { stdio: [null, process.stdout, process.stderr] }
  );
  tauriDriver.on('error', (error) => {
    console.error('tauri-driver error:', error);
    process.exit(1);
  });
  tauriDriver.on('exit', (code) => {
    if (!exit) {
      console.error('tauri-driver exited with code:', code);
      process.exit(1);
    }
  });


  const capabilities = new Capabilities();
  capabilities.set('tauri:options', { application });
  capabilities.setBrowserName('wry');


  // start the webdriver client
  driver = await new Builder()
    .withCapabilities(capabilities)
    .usingServer('http://127.0.0.1:4444/')
    .build();
});


after(async function () {
  // stop the webdriver session
  await closeTauriDriver();
});


describe('Hello Tauri', () => {
  it('should be cordial', async () => {
    const text = await driver.findElement(By.css('body > h1')).getText();
    expect(text).to.match(/^[hH]ello/);
  });


  it('should be excited', async () => {
    const text = await driver.findElement(By.css('body > h1')).getText();
    expect(text).to.match(/!$/);
  });


  it('should be easy on the eyes', async () => {
    // selenium returns color css values as rgb(r, g, b)
    const text = await driver
      .findElement(By.css('body'))
      .getCssValue('background-color');


    const rgb = text.match(/^rgb\((?<r>\d+), (?<g>\d+), (?<b>\d+)\)$/).groups;
    expect(rgb).to.have.all.keys('r', 'g', 'b');


    const luma = 0.2126 * rgb.r + 0.7152 * rgb.g + 0.0722 * rgb.b;
    expect(luma).to.be.lessThan(100);
  });
});


async function closeTauriDriver() {
  exit = true;
  // kill the tauri-driver process
  tauriDriver.kill();
  // stop the webdriver session
  await driver.quit();
}


function onShutdown(fn) {
  const cleanup = () => {
    try {
      fn();
    } finally {
      process.exit();
    }
  };


  process.on('exit', cleanup);
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
  process.on('SIGHUP', cleanup);
  process.on('SIGBREAK', cleanup);
}


onShutdown(() => {
  closeTauriDriver();
});
```
 If you are familiar with JS testing frameworks, `describe`, `it`, and `expect` should look familiar. We also have semi-complex `before()` and `after()` callbacks to set up and teardown mocha. Lines that are not the tests themselves have comments explaining the setup and teardown code. If you were familiar with the Spec file from the [WebdriverIO example](/develop/tests/webdriver/example/webdriverio/#spec), you notice a lot more code that isn’t tests, as we have to set up a few more WebDriver related items. ## Running the Test Suite Now that we are all set up with our dependencies and our test script, let’s run it! * npm 
  ```sh
  npm test
  ```
 * yarn 
  ```sh
  yarn test
  ```
 We should see output the following output: 
```text
➜  selenium git:(main) ✗ yarn test
yarn run v1.22.11
$ Mocha




  Hello Tauri
    ✔ should be cordial (120ms)
    ✔ should be excited
    ✔ should be easy on the eyes




  3 passing (588ms)


Done in 0.93s.
```
 We can see that our `Hello Tauri` test suite we created with `describe` had all 3 items we created with `it` pass their tests! With [Selenium](https://selenium.dev/) and some hooking up to a test suite, we just enabled e2e testing without modifying our Tauri application at all!

# WebdriverIO

Note Make sure to go through the [prerequisites instructions](/develop/tests/webdriver/manual-setup/) to be able to follow this guide. This WebDriver testing example will use [WebdriverIO](https://webdriver.io/), and its testing suite. It is expected to have Node.js already installed, along with `npm` or `yarn` although the [finished example project](https://github.com/tauri-apps/webdriver-example) uses `pnpm`. ## Create a Directory for the Tests Let’s create a space to write these tests in our project. We will be using a nested directory for this example project as we will later also go over other frameworks, but typically you only need to use one. Create the directory we will use with `mkdir e2e-tests`. The rest of this guide assumes you are inside the `e2e-tests` directory. ## Initializing a WebdriverIO Project We will be using a pre-existing `package.json` to bootstrap this test suite because we have already chosen specific [WebdriverIO](https://webdriver.io/) config options and want to showcase a simple working solution. The bottom of this section has a collapsed guide on setting it up from scratch. `package.json`: 
```json
{
  "name": "webdriverio",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "wdio run wdio.conf.js"
  },
  "dependencies": {
    "@wdio/cli": "^9.19.0"
  },
  "devDependencies": {
    "@wdio/local-runner": "^9.19.0,
    "@wdio/mocha-framework": "^9.19.0",
    "@wdio/spec-reporter": "^9.19.0"
  }
}
```
 We have a script that runs a [WebdriverIO](https://webdriver.io/) config as a test suite exposed as the `test` command. We also have various dependencies added by the `@wdio/cli` command when we first set it up. In short, these dependencies are for the most simple setup using a local WebDriver runner, [Mocha](https://mochajs.org/) as the test framework, and a simple Spec Reporter. ## Config You may have noticed that the `test` script in our `package.json` mentions a file `wdio.conf.js`. That’s the [WebdriverIO](https://webdriver.io/) config file which controls most aspects of our testing suite. `wdio.conf.js`: 
```javascript
import os from 'os';
import path from 'path';
import { spawn, spawnSync } from 'child_process';
import { fileURLToPath } from 'url';


const __dirname = fileURLToPath(new URL('.', import.meta.url));


// keep track of the `tauri-driver` child process
let tauriDriver;
let exit = false;


export const config = {
  host: '127.0.0.1',
  port: 4444,
  specs: ['./develop/tests/specs/**/*.js'],
  maxInstances: 1,
  capabilities: [
    {
      maxInstances: 1,
      'tauri:options': {
        application: '../src-tauri/target/debug/tauri-app',
      },
    },
  ],
  reporters: ['spec'],
  framework: 'mocha',
  mochaOpts: {
    ui: 'bdd',
    timeout: 60000,
  },


  // ensure the rust project is built since we expect this binary to exist for the webdriver sessions
  onPrepare: () => {
    // Remove the extra `--` if you're not using npm!
    spawnSync(
      'npm',
      ['run', 'tauri', 'build', '--', '--debug', '--no-bundle'],
      {
        cwd: path.resolve(__dirname, '..'),
        stdio: 'inherit',
        shell: true,
      }
    );
  },


  // ensure we are running `tauri-driver` before the session starts so that we can proxy the webdriver requests
  beforeSession: () => {
    tauriDriver = spawn(
      path.resolve(os.homedir(), '.cargo', 'bin', 'tauri-driver'),
      [],
      { stdio: [null, process.stdout, process.stderr] }
    );


    tauriDriver.on('error', (error) => {
      console.error('tauri-driver error:', error);
      process.exit(1);
    });
    tauriDriver.on('exit', (code) => {
      if (!exit) {
        console.error('tauri-driver exited with code:', code);
        process.exit(1);
      }
    });
  },


  // clean up the `tauri-driver` process we spawned at the start of the session
  // note that afterSession might not run if the session fails to start, so we also run the cleanup on shutdown
  afterSession: () => {
    closeTauriDriver();
  },
};


function closeTauriDriver() {
  exit = true;
  tauriDriver?.kill();
}


function onShutdown(fn) {
  const cleanup = () => {
    try {
      fn();
    } finally {
      process.exit();
    }
  };


  process.on('exit', cleanup);
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
  process.on('SIGHUP', cleanup);
  process.on('SIGBREAK', cleanup);
}


// ensure tauri-driver is closed when our test process exits
onShutdown(() => {
  closeTauriDriver();
});
```
 If you are interested in the properties on the `config` object, we [suggest reading the documentation](https://webdriver.io/docs/configurationfile). For non-WDIO specific items, there are comments explaining why we are running commands in `onPrepare`, `beforeSession`, and `afterSession`. We also have our specs set to `"./test/specs/**/*.js"`, so let’s create a spec now. ## Spec A spec contains the code that is testing your actual application. The test runner will load these specs and automatically run them as it sees fit. Let’s create our spec now in the directory we specified. `test/specs/example.e2e.js`: 
```javascript
// calculates the luma from a hex color `#abcdef`
function luma(hex) {
  if (hex.startsWith('#')) {
    hex = hex.substring(1);
  }


  const rgb = parseInt(hex, 16);
  const r = (rgb >> 16) & 0xff;
  const g = (rgb >> 8) & 0xff;
  const b = (rgb >> 0) & 0xff;
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}


describe('Hello Tauri', () => {
  it('should be cordial', async () => {
    const header = await $('body > h1');
    const text = await header.getText();
    expect(text).toMatch(/^[hH]ello/);
  });


  it('should be excited', async () => {
    const header = await $('body > h1');
    const text = await header.getText();
    expect(text).toMatch(/!$/);
  });


  it('should be easy on the eyes', async () => {
    const body = await $('body');
    const backgroundColor = await body.getCSSProperty('background-color');
    expect(luma(backgroundColor.parsed.hex)).toBeLessThan(100);
  });
});
```
 The `luma` function on top is just a helper function for one of our tests and is not related to the actual testing of the application. If you are familiar with other testing frameworks, you may notice similar functions being exposed that are used, such as `describe`, `it`, and `expect`. The other APIs, such as items like `$` and its exposed methods, are covered by the [WebdriverIO API docs](https://webdriver.io/docs/api). ## Running the Test Suite Now that we are all set up with config and a spec let’s run it! * npm 
  ```sh
  npm test
  ```
 * yarn 
  ```sh
  yarn test
  ```
 We should see output the following output: 
```text
➜  webdriverio git:(main) ✗ yarn test
yarn run v1.22.11
$ wdio run wdio.conf.js


Execution of 1 workers started at 2021-08-17T08:06:10.279Z


[0-0] RUNNING in undefined - /develop/tests/specs/example.e2e.js
[0-0] PASSED in undefined - /develop/tests/specs/example.e2e.js


 "spec" Reporter:
------------------------------------------------------------------
[wry 0.12.1 linux #0-0] Running: wry (v0.12.1) on linux
[wry 0.12.1 linux #0-0] Session ID: 81e0107b-4d38-4eed-9b10-ee80ca47bb83
[wry 0.12.1 linux #0-0]
[wry 0.12.1 linux #0-0] » /develop/tests/specs/example.e2e.js
[wry 0.12.1 linux #0-0] Hello Tauri
[wry 0.12.1 linux #0-0]    ✓ should be cordial
[wry 0.12.1 linux #0-0]    ✓ should be excited
[wry 0.12.1 linux #0-0]    ✓ should be easy on the eyes
[wry 0.12.1 linux #0-0]
[wry 0.12.1 linux #0-0] 3 passing (244ms)




Spec Files:   1 passed, 1 total (100% completed) in 00:00:01


Done in 1.98s.
```
 We see the Spec Reporter tell us that all 3 tests from the `test/specs/example.e2e.js` file, along with the final report `Spec Files: 1 passed, 1 total (100% completed) in 00:00:01`. Using the [WebdriverIO](https://webdriver.io/) test suite, we just easily enabled e2e testing for our Tauri application from just a few lines of configuration and a single command to run it! Even better, we didn’t have to modify the application at all.

# Manual setup

> Driving tauri-driver directly without the WebdriverIO Tauri service

This page covers driving [`tauri-driver`](https://crates.io/crates/tauri-driver) directly, without the [`@wdio/tauri-service`](https://webdriver.io/docs/desktop-testing/tauri). Reach for it if you are not using Node.js, prefer [Selenium](/develop/tests/webdriver/example/selenium/), or are integrating WebDriver into a custom test harness. For most projects the service is the easier path — it automates everything below and additionally supports macOS. See the [WebDriver overview](/develop/tests/webdriver/) to get started with it. When driving `tauri-driver` directly, only Windows and Linux are supported on desktop, as macOS has no WKWebView driver tool available. iOS and Android work through Appium 2, but the process is not currently streamlined. ## System Dependencies Install the latest [`tauri-driver`](https://crates.io/crates/tauri-driver) or update an existing installation by running: 
```shell
cargo install tauri-driver --locked
```
 Because we currently utilize the platform’s native [WebDriver](https://www.w3.org/TR/webdriver/) server, there are some requirements for running [`tauri-driver`](https://crates.io/crates/tauri-driver) on supported platforms. ### Linux We use `WebKitWebDriver` on Linux platforms. Check if this binary exists already by running the `which WebKitWebDriver` command as some distributions bundle it with the regular WebKit package. Other platforms may have a separate package for them, such as `webkit2gtk-driver` on Debian-based distributions. ### Windows Make sure to grab the version of [Microsoft Edge Driver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/) that matches your Windows Edge version that the application is being built and tested on. This should almost always be the latest stable version on up-to-date Windows installs. If the two versions do not match, you may experience your WebDriver testing suite hanging while trying to connect. You can use the [msedgedriver-tool](https://github.com/chippers/msedgedriver-tool) to download the appropriate Microsoft Edge Driver: 
```powershell
cargo install --git https://github.com/chippers/msedgedriver-tool
& "$HOME/.cargo/bin/msedgedriver-tool.exe"
```
 The download contains a binary called `msedgedriver.exe`. [`tauri-driver`](https://crates.io/crates/tauri-driver) looks for that binary in the `$PATH` so make sure it’s either available on the path or use the `--native-driver` option on [`tauri-driver`](https://crates.io/crates/tauri-driver). You may want to download this automatically as part of the CI setup process to ensure the Edge, and Edge Driver versions stay in sync on Windows CI machines. A guide on how to do this may be added at a later date. ## Example Applications Below are step-by-step guides to show how to create a minimal example application that is tested with WebDriver. If you prefer to see the result of the guide and look over a finished minimal codebase that utilizes it, you can look at <https://github.com/tauri-apps/webdriver-example>. [Selenium](/develop/tests/webdriver/example/selenium/) [WebdriverIO](/develop/tests/webdriver/example/webdriverio/) ## Continuous Integration (CI) The above examples also comes with a CI script to test with GitHub Actions, but you may still be interested in the below WebDriver CI guide as it explains the concept a bit more. [Continuous Integration (CI)](/develop/tests/webdriver/ci/)

# Updating Dependencies

## Update npm Packages If you are using the `tauri` package: * npm 
  ```sh
  npm install @tauri-apps/cli@latest @tauri-apps/api@latest
  ```
 * yarn 
  ```sh
  yarn up @tauri-apps/cli @tauri-apps/api
  ```
 * pnpm 
  ```sh
  pnpm update @tauri-apps/cli @tauri-apps/api --latest
  ```
 You can also detect what the latest version of Tauri is on the command line, using: * npm 
  ```sh
  npm outdated @tauri-apps/cli
  ```
 * yarn 
  ```sh
  yarn outdated @tauri-apps/cli
  ```
 * pnpm 
  ```sh
  pnpm outdated @tauri-apps/cli
  ```
 ## Update Cargo Packages You can check for outdated packages with [`cargo outdated`](https://github.com/kbknapp/cargo-outdated) or on the crates.io pages: [tauri](https://crates.io/crates/tauri/versions) / [tauri-build](https://crates.io/crates/tauri-build/versions). Go to `src-tauri/Cargo.toml` and change `tauri` and `tauri-build` to 
```toml
[build-dependencies]
tauri-build = "%version%"


[dependencies]
tauri = { version = "%version%" }
```
 where `%version%` is the corresponding version number from above. Then do the following: 
```shell
cd src-tauri
cargo update
```
 Alternatively, you can run the `cargo upgrade` command provided by [cargo-edit](https://github.com/killercup/cargo-edit) which does all of this automatically. ## Sync npm Packages and Cargo Crates versions Since the JavaScript APIs rely on Rust code in the backend, adding a new feature requires upgrading both sides to ensure compatibility. Please make sure you have the same minor version of the npm package `@tauri-apps/api` and cargo crate `tauri` synced And for the plugins, we might introduce this type of changes in patch releases, so we bump the npm package and cargo crate versions together, and you need to keep the exact versions synced, for example, you need the same version (e.g. `2.2.1`) of the npm package `@tauri-apps/plugin-fs` and cargo crate `tauri-plugin-fs`

# Distribute

> Information on the tooling you need to distribute your application either to the platform app stores or as platform-specific installers

Tauri provides the tooling you need to distribute your application either to the platform app stores or as platform-specific installers. ## Building Tauri builds your application directly from its CLI via the `build`, `android build` and `ios build` commands. * npm 
  ```sh
  npm run tauri build
  ```
 * yarn 
  ```sh
  yarn tauri build
  ```
 * pnpm 
  ```sh
  pnpm tauri build
  ```
 * deno 
  ```sh
  deno task tauri build
  ```
 * bun 
  ```sh
  bun tauri build
  ```
 * cargo 
  ```sh
  cargo tauri build
  ```
 See the [distributing](#distributing) section to learn more about the configuration options available for each bundle and how to distribute them to your users. Note Most platforms requires code signing. See the [signing](#signing) section for more information. ### Bundling By default the `build` command automatically bundles your application for the configured formats. If you need further customization on how the platform bundles are generated, you can split the build and bundle steps: * npm 
  ```sh
  npm run tauri build -- --no-bundle
  # bundle for distribution outside the macOS App Store
  npm run tauri bundle -- --bundles app,dmg
  # bundle for App Store distribution
  npm run tauri bundle -- --bundles app --config src-tauri/tauri.appstore.conf.json
  ```
 * yarn 
  ```sh
  yarn tauri build --no-bundle
  # bundle for distribution outside the macOS App Store
  yarn tauri bundle --bundles app,dmg
  # bundle for App Store distribution
  yarn tauri bundle --bundles app --config src-tauri/tauri.appstore.conf.json
  ```
 * pnpm 
  ```sh
  pnpm tauri build --no-bundle
  # bundle for distribution outside the macOS App Store
  pnpm tauri bundle --bundles app,dmg
  # bundle for App Store distribution
  pnpm tauri bundle --bundles app --config src-tauri/tauri.appstore.conf.json
  ```
 * deno 
  ```sh
  deno task tauri build --no-bundle
  # bundle for distribution outside the macOS App Store
  deno task tauri bundle --bundles app,dmg
  # bundle for App Store distribution
  deno task tauri bundle --bundles app --config src-tauri/tauri.appstore.conf.json
  ```
 * bun 
  ```sh
  bun tauri build --no-bundle
  # bundle for distribution outside the macOS App Store
  bun tauri bundle --bundles app,dmg
  # bundle for App Store distribution
  bun tauri bundle --bundles app --config src-tauri/tauri.appstore.conf.json
  ```
 * cargo 
  ```sh
  cargo tauri build --no-bundle
  # bundle for distribution outside the macOS App Store
  cargo tauri bundle --bundles app,dmg
  # bundle for App Store distribution
  cargo tauri bundle --bundles app --config src-tauri/tauri.appstore.conf.json
  ```
 ## Versioning Your application version can be defined in the [`tauri.conf.json > version`](/reference/config/#version) configuration option, which is the recommended way for managing the app version. If that config value is not set, Tauri uses the `package > version` value from your `src-tauri/Cargo.toml` file instead. Note Some platforms have some limitations and special cases for the version string. See the individual distribution documentation pages for more information. ## Signing Code signing enhances the security of your application by applying a digital signature to your application’s executables and bundles, validating your identity of the provider of your application. Signing is required on most platforms. See the documentation for each platform for more information. [macOS](/distribute/sign/macos/)Code signing and notarization for macOS apps [Windows](/distribute/sign/windows/)Code signing Windows installers [Linux](/distribute/sign/linux/)Code signing Linux packages [Android](/distribute/sign/android/)Code signing for Android [iOS](/distribute/sign/ios/)Code signing for iOS ## Distributing Learn how to distribute your application for each platform. ### Linux For Linux you can distribute your app using the Debian package, Snap, AppImage, Flatpak, RPM or Arch User Repository (AUR) formats. [AppImage](/distribute/appimage/)Distribute as an AppImage [AUR](/distribute/aur/)Publishing To The Arch User Repository [Debian](/distribute/debian/)Distribute as a Debian package [RPM](/distribute/rpm/)Distribute as an RPM package [Snapcraft](/distribute/snapcraft/)Distribute on Snapcraft.io [Code signing](/distribute/sign/linux/) ### macOS For macOS you can either distribute your application directly to the App Store or ship a DMG installer as direct download. Both methods require code signing, and distributing outside the App Store also requires notarization. [App Bundle](/distribute/macos-application-bundle/)Distribute macOS apps as an App Bundle [App Store](/distribute/app-store/)Distribute iOS and macOS apps to the App Store [DMG](/distribute/dmg/)Distribute macOS apps as Apple Disk Images [Code signing and notarization](/distribute/sign/macos/) ### Windows Learn how to distribute to the Microsoft Store or configure a Windows installer. [Microsoft Store](/distribute/microsoft-store/)Distribute Windows apps to the Microsoft Store [Windows Installer](/distribute/windows-installer/)Distribute installers for Windows [Code signing](/distribute/sign/windows/) ### Android Distribute your Android application to Google Play. [Google Play](/distribute/google-play/)Distribute Android apps to Google Play [Code signing](/distribute/sign/android/) ### iOS Learn how to upload your application to the App Store. [App Store](/distribute/app-store/)Distribute iOS and macOS apps to the App Store [Code signing](/distribute/sign/ios/) ### Cloud Services Distribute your application to Cloud services that globally distribute your application and support auto updates out of the box. [CrabNebula Cloud](/distribute/crabnebula-cloud/)Distribute your app using CrabNebula

# App Store

The [Apple App Store](https://www.apple.com/store) is the app marketplace maintained by Apple. You can distribute your Tauri app targeting macOS and iOS via this App Store. This guide only covers details for distributing apps directly to the App Store. See the general [App Bundle](/distribute/macos-application-bundle/) for more information on macOS distribution options and configurations. ## Requirements Distributing iOS and macOS apps requires enrolling to the [Apple Developer](https://developer.apple.com) program. Additionally, you must setup code signing for [macOS](/distribute/sign/macos/) and [iOS](/distribute/sign/ios/). ## Changing App Icon After running `tauri ios init` to setup the Xcode project, you can use the `tauri icon` command to update the app icons. * npm 
  ```sh
  npm run tauri icon /path/to/app-icon.png -- --ios-color '#fff'
  ```
 * yarn 
  ```sh
  yarn tauri icon /path/to/app-icon.png --ios-color '#fff'
  ```
 * pnpm 
  ```sh
  pnpm tauri icon /path/to/app-icon.png --ios-color '#fff'
  ```
 * deno 
  ```sh
  deno task tauri icon /path/to/app-icon.png --ios-color '#fff'
  ```
 * bun 
  ```sh
  bun tauri icon /path/to/app-icon.png --ios-color '#fff'
  ```
 * cargo 
  ```sh
  cargo tauri icon /path/to/app-icon.png --ios-color '#fff'
  ```
 The `--ios-color` argument defines the background color for the iOS icons. ## Setting up After enrolling to the Apple Developer program, the first step to distribute your Tauri app in the App Store is to register your app in the [App Store Connect](https://appstoreconnect.apple.com/apps). Note The value provided in the *Bundle ID* field **must** match the identifier defined in [`tauri.conf.json > identifier`](/reference/config/#identifier). ## Build and upload The Tauri CLI can package your app for macOS and iOS. Running on a macOS machine is a requirement. Tauri derives the [`CFBundleVersion`](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleversion) from the value defined in \[`tauri.conf.json > version`]. You can set a custom bundle version in the \[`tauri.conf.json > bundle > iOS > bundleVersion`] or \[`tauri.conf.json > bundle > macOS > bundleVersion`] configuration if you need a different bundle version scheme e.g. sequential codes: tauri.conf.json 
```diff
{
  "bundle": {
    "iOS": {
      +"bundleVersion": "100"
    }
  }
}
```
 Caution Code signing is required. See the documentation for [macOS](/distribute/sign/macos/) and [iOS](/distribute/sign/ios/). Note that Tauri leverages Xcode for the iOS app so you can use Xcode to archive and distribute for iOS instead of the Tauri CLI. To open the iOS project in Xcode for building you must run the following command: * npm 
  ```sh
  npm run tauri ios build -- --open
  ```
 * yarn 
  ```sh
  yarn tauri ios build --open
  ```
 * pnpm 
  ```sh
  pnpm tauri ios build --open
  ```
 * deno 
  ```sh
  deno task tauri ios build --open
  ```
 * bun 
  ```sh
  bun tauri ios build --open
  ```
 * cargo 
  ```sh
  cargo tauri ios build --open
  ```
 ### macOS To upload your app to the App Store, first you must ensure all required configuration options are set so you can package the App Bundle, create a signed `.pkg` file and upload it. The following sections will guide you through the process. #### Setup Your app must include some configurations to be accepted by the App Store verification system. * Category Your app must define its [`tauri.conf.json > bundle > category`](/reference/config/#category) to be displayed in the App Store: tauri.conf.json 
```diff
{
  "bundle": {
    +"category": "Utility"
  }
}
```
 * Provisioning profile You must also create a provisioning profile for your app to be accepted by Apple. In the [Identifiers](https://developer.apple.com/account/resources/identifiers/list) page, create a new App ID and make sure its “Bundle ID” value matches the identifier set in [`tauri.conf.json > identifier`](/reference/config/#identifier). Navigate to the [Profiles](https://developer.apple.com/account/resources/profiles/list) page to create a new provisioning profile. For App Store macOS distribution, it must be a “Mac App Store Connect” profile. Select the appropriate App ID and link the certificate you are using for code signing. After creating the provisioning profile, download it and save it to a known location and configure Tauri to include it in your app bundle: tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      +"files": {
        +"embedded.provisionprofile": "path/to/profile-name.provisionprofile"
+      }
    }
  }
}
```
 * Info.plist Your app must comply with encryption export regulations. See the [official documentation](https://developer.apple.com/documentation/security/complying-with-encryption-export-regulations?language=objc) for more information. Create a Info.plist file in the src-tauri folder: 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>ITSAppUsesNonExemptEncryption</key>
  <false/> # or `true` if your app uses encryption
</dict>
</plist>
```
 * Entitlements Your app must include the App Sandbox capability to be distributed in the App Store. Additionally, you must also set your App ID and Team ID in the code signing entitlements. Create a `Entitlements.plist` file in the `src-tauri` folder: 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.application-identifier</key>
    <string>$TEAM_ID.$IDENTIFIER</string>
    <key>com.apple.developer.team-identifier</key>
    <string>$TEAM_ID</string>
</dict>
</plist>
```
 Note that you must replace `$IDENTIFIER` with the [`tauri.conf.json > identifier`](/reference/config/#identifier) value and `$TEAM_ID` with your Apple Developer team ID, which can be found in the `App ID Prefix` section in the [Identifier](https://developer.apple.com/account/resources/identifiers/list) you created for the provisioning profile. And reference that file in the macOS bundle configuration [`tauri.conf.json > bundle > macOS > entitlements`](/reference/config/#entitlements): tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      +"entitlements": "./Entitlements.plist"
    }
  }
}
```
 You now must build your application with code signing enabled for the entitlements to apply. Make sure your app works when running in an App Sandbox context. #### Build You must upload your macOS application as a `.pkg` file to the App Store. Run the following command to package your app as a macOS App Bundle (`.app` extension): * npm 
  ```sh
  npm run tauri build -- --bundles app --target universal-apple-darwin
  ```
 * yarn 
  ```sh
  yarn tauri build --bundles app --target universal-apple-darwin
  ```
 * pnpm 
  ```sh
  pnpm tauri build --bundles app --target universal-apple-darwin
  ```
 * deno 
  ```sh
  deno task tauri build --bundles app --target universal-apple-darwin
  ```
 * bun 
  ```sh
  bun tauri build --bundles app --target universal-apple-darwin
  ```
 * cargo 
  ```sh
  cargo tauri build --bundles app --target universal-apple-darwin
  ```
 Note The above command creates an Universal App Binary application, supporting both Apple Silicon and Intel processors. If you prefer to only support Apple Silicon instead, you must change [`tauri.conf.json > bundle > macOS > minimumSystemVersion`](/reference/config/#minimumsystemversion) to `12.0`: tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      +"minimumSystemVersion": "12.0"
    }
  }
}
```
 And change the CLI command and output path based on the Mac system you are running: * if your build system uses an Apple Silicon chip, remove the `--target universal-apple-darwin` arguments and use `target/release` instead of `target/universal-apple-darwin/release` in the paths referenced below. * if your build system uses an Intel chip: * install the Rust Apple Silicon target: 
    ```plaintext
    rustup target add aarch64-apple-darwin
    ```
 * change the `universal-apple-darwin` argument to `aarch64-apple-darwin` and use `target/aarch64-apple-darwin/release` instead of `target/universal-apple-darwin/release` in the paths referenced below. See the [App Bundle distribution guide](/distribute/macos-application-bundle/) for more information on configuration options. To generate a signed `.pkg` from your app bundle, run the following command: 
```plaintext
xcrun productbuild --sign "<certificate signing identity>" --component "target/universal-apple-darwin/release/bundle/macos/$APPNAME.app" /Applications "$APPNAME.pkg"
```
 Note that you must replace *$APPNAME* with your app name. Note You must sign the PKG with a *Mac Installer Distribution* signing certificate. #### Upload Now you can use the [`altool`](https://help.apple.com/itc/apploader/#/apdATD1E53-D1E1A1303-D1E53A1126) CLI to upload your app PKG to the App Store: 
```plaintext
xcrun altool --upload-app --type macos --file "$APPNAME.pkg" --apiKey $APPLE_API_KEY_ID --apiIssuer $APPLE_API_ISSUER
```
 Note that `altool` requires an App Store Connect API key to upload your app. See the [authentication section](#authentication) for more information. Your app will then be validated by Apple and available in TestFlight if approved. ### iOS To build your iOS app, run the `tauri ios build` command: * npm 
  ```sh
  npm run tauri ios build -- --export-method app-store-connect
  ```
 * yarn 
  ```sh
  yarn tauri ios build --export-method app-store-connect
  ```
 * pnpm 
  ```sh
  pnpm tauri ios build --export-method app-store-connect
  ```
 * deno 
  ```sh
  deno task tauri ios build --export-method app-store-connect
  ```
 * bun 
  ```sh
  bun tauri ios build --export-method app-store-connect
  ```
 * cargo 
  ```sh
  cargo tauri ios build --export-method app-store-connect
  ```
 The generated IPA file can be found in `src-tauri/gen/apple/build/arm64/$APPNAME.ipa`. Note that you must replace *$APPNAME* with your app name. Now you can use the `altool` CLI to upload your iOS app to the App Store: 
```plaintext
xcrun altool --upload-app --type ios --file "src-tauri/gen/apple/build/arm64/$APPNAME.ipa" --apiKey $APPLE_API_KEY_ID --apiIssuer $APPLE_API_ISSUER
```
 Note that `altool` requires an App Store Connect API key to upload your app. See the [authentication section](#authentication) for more information. Your app will then be validated by Apple and available in TestFlight if approved. ### Authentication The iOS and macOS apps are uploaded using `altool`, which uses an App Store Connect API key to authenticate. To create a new API key, open the [App Store Connect’s Users and Access page](https://appstoreconnect.apple.com/access/users), select the Integrations > Individual Keys tab, click on the Add button and select a name and the Developer access. The `APPLE_API_ISSUER` (Issuer ID) is presented above the keys table, and the `APPLE_API_KEY_ID` is the value on the Key ID column on that table. You also need to download the private key, which can only be done once and is only visible after a page reload (the button is shown on the table row for the newly created key). The private key file path must be saved as `AuthKey\_<APPLE_API_KEY_ID>.p8` in one of these directories:`<current-working-directory>/private_keys`, `~/private_keys`, `~/.private_keys`or`~/.appstoreconnect/private_keys`.

# AppImage

`AppImage` is a distribution format that does not rely on the system installed packages and instead bundles all dependencies and files needed by the application. For this reason, the output file is larger but easier to distribute since it is supported on many Linux distributions and can be executed without installation. The user just needs to make the file executable (`chmod a+x MyProject.AppImage`) and can then run it (`./MyProject.AppImage`). AppImages are convenient, simplifying the distribution process if you cannot make a package targeting the distribution’s package manager. Still, you should carefully use it as the file size grows from the 2-6 MB range to 70+ MB. Note GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri’s [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue. ## Limitations Core libraries such as glibc frequently break compatibility with older systems. For this reason, you must build your Tauri application using the oldest base system you intend to support that also provides Tauri v2’s required WebKitGTK 4.1 packages. Ubuntu 22.04 and Debian 12 are suitable baseline examples because they provide `libwebkit2gtk-4.1-dev` from their standard package repositories. Building on a newer base system can raise the minimum glibc version required by your app, so when running on an older system, you may face a runtime error like `/usr/lib/libc.so.6: version 'GLIBC_2.33' not found`. We recommend using a Docker container or GitHub Actions to build your Tauri application for Linux. See the issues [tauri-apps/tauri#1355](https://github.com/tauri-apps/tauri/issues/1355) and [rust-lang/rust#57497](https://github.com/rust-lang/rust/issues/57497), in addition to the [AppImage guide](https://docs.appimage.org/reference/best-practices.html#binaries-compiled-on-old-enough-base-system) for more information. ## Multimedia support via GStreamer If your app plays audio/video you need to enable `tauri.conf.json > bundle > linux > appimage > bundleMediaFramework`. This will increase the size of the AppImage bundle to include additional gstreamer files needed for media playback. This flag is currently only fully supported on Ubuntu build systems. Make sure that your build system has all the plugins your app may need at runtime. Caution GStreamer plugins in the `ugly` package are licensed in a way that may make it hard to distribute them as part of your app. ## Custom Files To include custom files in the AppImage that you do not want to include via Tauri’s [`resources` feature](/develop/resources/), you can provide a list of files or folders in `tauri.conf.json > bundle > linux > appimage > files`. The configuration object maps the path in the AppImage to the path to the file on your filesystem, relative to the `tauri.conf.json` file. Here’s an example configuration: tauri.conf.json 
```json
{
  "bundle": {
    "linux": {
      "appimage": {
        "files": {
          "/usr/share/README.md": "../README.md", // copies the ../README.md file to <appimage>/usr/share/README.md
          "/usr/assets": "../assets/" // copies the entire ../assets directory to <appimage>/usr/assets
        }
      }
    }
  }
}
```
 Note Note that the destination paths must currently begin with `/usr/`. ## AppImages for ARM-based devices August 2025 Update Github has [released](https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/#get-started) publicly available `ubuntu-22.04-arm` and `ubuntu-24.04-arm` runners. You can use these to build your app with no changes, a typical build should take \~10 minutes. `linuxdeploy`, the AppImage tooling Tauri uses, currently [does not support cross-compiling](https://github.com/linuxdeploy/linuxdeploy/issues/258) ARM AppImages. This means ARM AppImages can only be built on ARM devices or emulators. Check out our [GitHub Action guide](/distribute/pipelines/github/#arm-runner-compilation) for an example workflow that leverages QEMU to build the app. Note that this is extremely slow and only recommended in public repositories where Build Minutes are free. In private repositories GitHub’s ARM runners should be more cost-efficient and much easier to set up.

# AUR

# Publishing to the Arch User Repository ## Setup First go to `https://aur.archlinux.org` and make an account. Be sure to add the proper ssh keys. Next, clone an empty git repository using this command. 
```sh
git clone https://aur.archlinux.org/your-repo-name
```
 After completing the steps above, create a file with the name `PKGBUILD`. Once the file is created you can move onto the next step. ### Writing a PKGBUILD file PKGBUILD 
```ini
pkgname=<pkgname>
pkgver=1.0.0
pkgrel=1
pkgdesc="Description of your app"
arch=('x86_64' 'aarch64')
url="https://github.com/<user>/<project>"
license=('MIT')
depends=('cairo' 'desktop-file-utils' 'gdk-pixbuf2' 'glib2' 'gtk3' 'hicolor-icon-theme' 'libsoup' 'pango' 'webkit2gtk-4.1')
options=('!strip' '!emptydirs')
install=${pkgname}.install
source_x86_64=("${url}/releases/download/v${pkgver}/appname_${pkgver}_amd64.deb")
source_aarch64=("${url}/releases/download/v${pkgver}/appname_${pkgver}_arm64.deb")
```
 * At the top of the file, define your package name and assign it the variable `pkgname`. * Set your `pkgver` variable. Typically it is best to use this variable in the source variable to increase maintainability. * The `pkgdesc` variable on your aur repo’s page and tells visitors what your app does. * The `arch` variable controls what architectures can install your package. * The `url` variable, while not required, helps to make your package appear more professional. * The `install` variable specifies the name of .install script which will be run when the package is installed, removed or upgraded. * The `depends` variable includes a list of items that are required to make your app run. For any Tauri app you must include all of the dependencies shown above. * The `source` variable is required and defines the location where your upstream package is. You can make a `source` architecture specific by adding the architecture to the end of the variable name. ### Generating `.SRCINFO` In order to push your repo to the aur you must generate an `.SRCINFO` file. This can be done with this command. 
```sh
makepkg --printsrcinfo > .SRCINFO
```
 ### Testing Testing the app is extremely simple. All you have to do is run `makepkg` within the same directory as the `PKGBUILD` file and see if it works ### Publishing Finally, after the testing phase is over, you can publish the application to AUR (Arch User Repository) with these commands. 
```sh
git add .


git commit -m "Initial Commit"


git push
```
 If all goes well, your repository should now appear on the AUR website. ## Examples ### Extracting From A Debian Package PKGBUILD 
```ini
# Maintainer:
# Contributor:
pkgname=<pkgname>
pkgver=1.0.0
pkgrel=1
pkgdesc="Description of your app"
arch=('x86_64' 'aarch64')
url="https://github.com/<user>/<project>"
license=('MIT')
depends=('cairo' 'desktop-file-utils' 'gdk-pixbuf2' 'glib2' 'gtk3' 'hicolor-icon-theme' 'libsoup' 'pango' 'webkit2gtk-4.1')
options=('!strip' '!debug')
install=${pkgname}.install
source_x86_64=("${url}/releases/download/v${pkgver}/appname_${pkgver}_amd64.deb")
source_aarch64=("${url}/releases/download/v${pkgver}/appname_${pkgver}_arm64.deb")
sha256sums_x86_64=('ca85f11732765bed78f93f55397b4b4cbb76685088553dad612c5062e3ec651f')
sha256sums_aarch64=('ed2dc3169d34d91188fb55d39867713856dd02a2360ffe0661cb2e19bd701c3c')
package() {
  # Extract package data
  tar -xvf data.tar.gz -C "${pkgdir}"


}
```
 my-tauri-app.install 
```ini
post_install() {
  gtk-update-icon-cache -q -t -f usr/share/icons/hicolor
  update-desktop-database -q
}


post_upgrade() {
  post_install
}


post_remove() {
  gtk-update-icon-cache -q -t -f usr/share/icons/hicolor
  update-desktop-database -q
}
```
 ### Building from source PKGBUILD 
```ini
# Maintainer:
pkgname=<pkgname>-git
pkgver=<pkgver>
pkgrel=1
pkgdesc="Description of your app"
arch=('x86_64' 'aarch64')
url="https://github.com/<user>/<project>"
license=('MIT')
depends=('cairo' 'desktop-file-utils' 'gdk-pixbuf2' 'glib2' 'gtk3' 'hicolor-icon-theme' 'libsoup' 'pango' 'webkit2gtk-4.1')
makedepends=('git' 'openssl' 'appmenu-gtk-module' 'libappindicator-gtk3' 'librsvg' 'cargo' 'pnpm' 'nodejs')
provides=('<pkgname>')
conflicts=('<binname>' '<pkgname>')
source=("git+${url}.git")
sha256sums=('SKIP')


pkgver() {
  cd <project>
  ( set -o pipefail
    git describe --long --abbrev=7 2>/dev/null | sed 's/\([^-]*-g\)/r\1/;s/-/./g' ||
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short=7 HEAD)"
  )
}


prepare() {
  cd <project>
  pnpm install
}


build() {
  cd <project>
  pnpm tauri build -b deb
}


package() {
  cp -a <project>/src-tauri/target/release/bundle/deb/<project>_${pkgver}_*/data/* "${pkgdir}"
}
```

# Distributing with CrabNebula Cloud

[CrabNebula](https://crabnebula.dev) is an official Tauri partner providing services and tooling for Tauri applications. The [CrabNebula Cloud](https://crabnebula.dev/cloud/) is a platform for application distribution that seamlessly integrates with the Tauri updater. The Cloud offers a Content Delivery Network (CDN) that is capable of shipping your application installers and updates globally while being cost effective and exposing download metrics. With the CrabNebula Cloud service it is simple to implement multiple release channels, download buttons for your application website and more. Setting up your Tauri app to use the Cloud is easy: all you need to do is to sign in to the [Cloud website](https://web.crabnebula.cloud/) using your GitHub account, create your organization and application and install its CLI to create a release and upload the Tauri bundles. Additionally, a [GitHub Action](https://github.com/crabnebula-dev/cloud-release/) is provided to simplify the process of using the CLI on GitHub workflows. For more information, see the [CrabNebula Cloud documentation](https://docs.crabnebula.dev/cloud/).

# Debian

The stock Debian package generated by the Tauri bundler has everything you need to ship your application to Debian-based Linux distributions, defining your application’s icons, generating a Desktop file, and specifying the dependencies `libwebkit2gtk-4.1-0` and `libgtk-3-0`, along with `libappindicator3-1` if your app uses the system tray. Note GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri’s [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue. ## Limitations Core libraries such as glibc frequently break compatibility with older systems. For this reason, you must build your Tauri application using the oldest base system you intend to support that also provides Tauri v2’s required WebKitGTK 4.1 packages. Ubuntu 22.04 and Debian 12 are suitable baseline examples because they provide `libwebkit2gtk-4.1-dev` from their standard package repositories. Building on a newer base system can raise the minimum glibc version required by your app, so when running on an older system, you may face a runtime error like `/usr/lib/libc.so.6: version 'GLIBC_2.33' not found`. We recommend using a Docker container or GitHub Actions to build your Tauri application for Linux. See the issues [tauri-apps/tauri#1355](https://github.com/tauri-apps/tauri/issues/1355) and [rust-lang/rust#57497](https://github.com/rust-lang/rust/issues/57497), in addition to the [AppImage guide](https://docs.appimage.org/reference/best-practices.html#binaries-compiled-on-old-enough-base-system) for more information. ## Custom Files Tauri exposes a few configurations for the Debian package in case you need more control. If your app depends on additional system dependencies you can specify them in `tauri.conf.json > bundle > linux > deb`. To include custom files in the Debian package, you can provide a list of files or folders in `tauri.conf.json > bundle > linux > deb > files`. The configuration object maps the path in the Debian package to the path to the file on your filesystem, relative to the `tauri.conf.json` file. Here’s an example configuration: 
```json
{
  "bundle": {
    "linux": {
      "deb": {
        "files": {
          "/usr/share/README.md": "../README.md", // copies the README.md file to /usr/share/README.md
          "/usr/share/assets": "../assets/" // copies the entire assets directory to /usr/share/assets
        }
      }
    }
  }
}
```
 ## Cross-Compiling for ARM-based Devices This guide covers manual compilation. Check out our [GitHub Action guide](/distribute/pipelines/github/#arm-runner-compilation) for an example workflow that leverages QEMU to build the app. This will be much slower but will also be able to build AppImages. Manual compilation is suitable when you don’t need to compile your application frequently and prefer a one-time setup. The following steps expect you to use a Linux distribution based on Debian/Ubuntu. 1. #### Install Rust targets for your desired architecture * For ARMv7 (32-bit): `rustup target add armv7-unknown-linux-gnueabihf` * For ARMv8 (ARM64, 64-bit): `rustup target add aarch64-unknown-linux-gnu` 2. #### Install the corresponding linker for your chosen architecture * For ARMv7: `sudo apt install gcc-arm-linux-gnueabihf` * For ARMv8 (ARM64): `sudo apt install gcc-aarch64-linux-gnu` 3. #### Open or create the file `<project-root>/.cargo/config.toml` and add the following configurations accordingly 
   ```toml
   [target.armv7-unknown-linux-gnueabihf]
   linker = "arm-linux-gnueabihf-gcc"


   [target.aarch64-unknown-linux-gnu]
   linker = "aarch64-linux-gnu-gcc"
   ```
 4. #### Enable the respective architecture in the package manager * For ARMv7: `sudo dpkg --add-architecture armhf` * For ARMv8 (ARM64): `sudo dpkg --add-architecture arm64` 5. #### Adjusting Package Sources On Debian, this step should not be necessary, but on other distributions, you might need to edit /etc/apt/sources.list to include the ARM architecture variant. For example on Ubuntu 22.04 add these lines to the bottom of the file (Remember to replace jammy with the codename of your Ubuntu version): 
   ```plaintext
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-backports main restricted universe multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security multiverse
   ```
 Then, to prevent issues with the main packages, you have to add the correct main architecture to all other lines the file contained beforehand. For standard 64-bit systems you need to add \[arch=amd64], the full file on Ubuntu 22.04 then looks similar to this: Show solution 
   ```plaintext
   # See http://help.ubuntu.com/community/UpgradeNotes for how to upgrade to
   # newer versions of the distribution.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy main restricted
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy main restricted


   ## Major bug fix updates produced after the final release of the
   ## distribution.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted


   ## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
   ## team. Also, please note that software in universe WILL NOT receive any
   ## review or updates from the Ubuntu security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy universe
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy universe
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates universe
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-updates universe


   ## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
   ## team, and may not be under a free licence. Please satisfy yourself as to
   ## your rights to use the software. Also, please note that software in
   ## multiverse WILL NOT receive any review or updates from the Ubuntu
   ## security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy multiverse
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy multiverse
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates multiverse


   ## N.B. software from this repository may not have been tested as
   ## extensively as that contained in the main release, although it includes
   ## newer versions of some applications which may provide useful features.
   ## Also, please note that software in backports WILL NOT receive any review
   ## or updates from the Ubuntu security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-backports main restricted universe multiverse
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-backports main restricted universe multiverse


   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security main restricted
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security main restricted
   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security universe
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security universe
   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security multiverse
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security multiverse


   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-backports main restricted universe multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security multiverse
   ```
 6. #### Update the package information: `sudo apt-get update && sudo apt-get upgrade -y` 7. #### Install the required webkitgtk library for your chosen architecture * For ARMv7: `sudo apt install libwebkit2gtk-4.1-dev:armhf` * For ARMv8 (ARM64): `sudo apt install libwebkit2gtk-4.1-dev:arm64` 8. #### Install OpenSSL or use a vendored version This is not always required so you may want to proceed first and check if you see errors like `Failed to find OpenSSL development headers`. * Either install the development headers system-wide: * For ARMv7: `sudo apt install libssl-dev:armhf` * For ARMv8 (ARM64): `sudo apt install libssl-dev:arm64` * Or enable the vendor feature for the OpenSSL Rust crate which will affect all other Rust dependencies using the same minor version. You can do so by adding this to the dependencies section in your `Cargo.toml` file: 
   ```toml
   openssl-sys = {version = "0.9", features = ["vendored"]}
   ```
 9. #### Set the `PKG_CONFIG_SYSROOT_DIR` to the appropriate directory based on your chosen architecture * For ARMv7: `export PKG_CONFIG_SYSROOT_DIR=/usr/arm-linux-gnueabihf/` * For ARMv8 (ARM64): `export PKG_CONFIG_SYSROOT_DIR=/usr/aarch64-linux-gnu/` 10. #### Build the app for your desired ARM version * For ARMv7: cargo tauri build –target armv7-unknown-linux-gnueabihf * For ARMv8 (ARM64): cargo tauri build –target aarch64-unknown-linux-gnu Choose the appropriate set of instructions based on whether you want to cross-compile your Tauri application for ARMv7 or ARMv8 (ARM64). Please note that the specific steps may vary depending on your Linux distribution and setup.

# DMG

The DMG (Apple Disk Image) format is a common macOS installer file that wraps your [App Bundle](/distribute/macos-application-bundle/) in a user-friendly installation window. The installer window includes your app icon and the Applications folder icon, where the user is expected to drag the app icon to the Applications folder icon to install it. It is the most common installation method for macOS applications distributed outside the App Store. This guide only covers details for distributing apps outside the App Store using the DMG format. See the [App Bundle distribution guide](/distribute/macos-application-bundle/) for more information on macOS distribution options and configurations. To distribute your macOS app in the App Store, see the [App Store distribution guide](/distribute/app-store/). To create an Apple Disk Image for your app you can use the Tauri CLI and run the `tauri build` command in a Mac computer: * npm 
  ```sh
  npm run tauri build -- --bundles dmg
  ```
 * yarn 
  ```sh
  yarn tauri build --bundles dmg
  ```
 * pnpm 
  ```sh
  pnpm tauri build --bundles dmg
  ```
 * deno 
  ```sh
  deno task tauri build --bundles dmg
  ```
 * bun 
  ```sh
  bun tauri build --bundles dmg
  ```
 * cargo 
  ```sh
  cargo tauri build --bundles dmg
  ```
 ![Standard DMG window](/_astro/standard-dmg-light.DwnO_utB_2qN4sD.webp) ![Standard DMG window](/_astro/standard-dmg-dark.DDFg0R9E_Z1Ofxfz.webp) Note GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri’s [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue. ## Window background You can set a custom background image to the DMG installation window with the \[`tauri.conf.json > bundle > macOS > dmg > background`] configuration option: tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      +"dmg": {
        +"background": "./images/"
+      }
    }
  }
}
```
 For instance your DMG background image can include an arrow to indicate to the user that it must drag the app icon to the Applications folder. ## Window size and position The default window size is 660x400. If you need a different size to fit your custom background image, set the \[`tauri.conf.json > bundle > macOS > dmg > windowSize`] configuration: tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      "dmg": {
        +"windowSize": {
          +"width": 800,
          +"height": 600
+        }
      }
    }
  }
}
```
 Additionally you can set the initial window position via \[`tauri.conf.json > bundle > macOS > dmg > windowPosition`]: tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      "dmg": {
        +"windowPosition": {
          +"x": 400,
          +"y": 400
+        }
      }
    }
  }
}
```
 ## Icon position You can change the app and *Applications folder* icon position with the [appPosition](/reference/config/#appposition) and [applicationFolderPosition](/reference/config/#applicationfolderposition) configuration values respectively: tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      "dmg": {
        +"appPosition": {
          +"x": 180,
          +"y": 220
+        },
        +"applicationFolderPosition": {
          +"x": 480,
          +"y": 220
+        }
      }
    }
  }
}
```
 Caution Due to a known issue, icon sizes and positions are not applied when creating DMGs on CI/CD platforms. See [tauri-apps/tauri#1731](https://github.com/tauri-apps/tauri/issues/1731) for more information.

# Flathub

* Open Source 1. Get your required tools. 
  ```sh
  git submodule add https://github.com/flatpak/flatpak-builder-tools.git
  cd flatpak-builder-tools/node/flatpak_node_generator
  pipx install . # Change this to your preferred installation method
  ```
 2. Generate your sources * Yarn 
    ```sh
    # Generate your Node Sources
    flatpak-node-generator --no-requests-cache -o node-sources.json yarn /path/to/your/lock/file/yarn.lock


    # Generate your cargo sources


    python3 flatpak-builder-tools/cargo/flatpak-cargo-generator.py -o cargo-sources.json src-tauri/Cargo.lock
    ```
 * NPM 
    ```sh
    # Generate your Node Sources
    flatpak-node-generator --no-requests-cache -o node-sources.json npm /path/to/your/lock/file/package-lock.json


    # Generate your cargo sources
    python3 flatpak-builder-tools/cargo/flatpak-cargo-generator.py -o cargo-sources.json src-tauri/Cargo.lock
    ```
 3. Create your metainfo Make sure to replace the relevant fields. 
  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  <component type="desktop-application">
      <id>org.your.id</id>
      <launchable type="desktop-id">org.your.id.desktop</launchable>
      <name>Your Apps Name</name>
      <developer id="io.github.roseblume.rosemusic">
          <name>Your Name</name>
      </developer>
      <content_rating type="oars-1.1">
      </content_rating>
      <keywords>
          <keyword>Keyword1</keyword>
          <keyword>Keyword2</keyword>
      </keywords>
      <branding>
          <color type="primary" scheme_preference="light">#00ffff</color>
          <color type="primary" scheme_preference="dark">#0c9aff</color>
      </branding>
      <recommends>
          <display_length compare="ge">360</display_length>
      </recommends>
      <summary>Your Summary</summary>


      <metadata_license>MIT</metadata_license>
      <project_license>MIT</project_license>
      <url type="homepage">https://github.com/Your-Username/Your-Repo</url>


      <supports>
          <control>pointing</control>
          <control>keyboard</control>
          <control>touch</control>
      </supports>


      <description>
          <p>
              Your Description
          </p>
      </description>
      <screenshots>
          <screenshot type="default">
              <image>https://site.com/your-image.png</image>
              <caption>Your Caption</caption>
          </screenshot>
      </screenshots>
      <releases>
          <release version="1.0.0" date="2024-11-02" >
              <description>
              <ul>
                  <li>Updated UI</li>
                  <li>Added Electronic Genre</li>
              </ul>
              </description>
          </release>
      </releases>
      <update_contact>your-email@place.com</update_contact>


  </component>
  ```
 Your metadata is recommended to be included into your debian bundle although it is not required. This can be done by adjusting your bundle configuration like so. 
  ```json
  "linux": {
        "deb": {
          "files": {
            "/usr/share/metainfo/org.your.id.metainfo.xml": "relative/path/from/your/tauri.conf.json/to/your/org.your.id.metainfo.xml"
          }
        }
      }
  ```
 4. Create your manifest 
  ```yaml
  id: org.your.id


  runtime: org.gnome.Platform
  runtime-version: '51'
  sdk: org.gnome.Sdk


  command: tauri-app
  finish-args:


  - --socket=wayland # Permission needed to show the window
  - --socket=fallback-x11 # Permission needed to show the window on legacy windowing systems
  - --device=dri # OpenGL, not necessary for all projects
  - --share=ipc
    sdk-extensions:
  - org.freedesktop.Sdk.Extension.node20
  - org.freedesktop.Sdk.Extension.rust-stable
    build-options:
    append-path: /usr/lib/sdk/node20/bin:/usr/lib/sdk/rust-stable/bin


  modules:


  - name: your-command
    buildsystem: simple
    env:
    HOME: /run/build/your-module
    CARGO_HOME: /run/build/your-module/src-tauri
    XDG_CACHE_HOME: /run/build/your-module/flatpak-node/cache
    yarn_config_offline: 'true'
    yarn_config_cache: /run/build/your-module/flatpak-node/yarn-cache
    sources:
    - type: git
      url: https://github.com/Your-Github-Username/Your-Git-Repo.git
      tag: v1.2.2
    - cargo-sources.json
    - node-sources.json
      build-commands:
    - echo -e 'yarn-offline-mirror "/run/build/your-module/flatpak-node/yarn-mirror"\nyarn-offline-mirror-pruning true' > /run/build/your-module/.yarnrc
    - mkdir -p src-tauri/.cargo && echo -e '[source.crates-io]\nreplace-with = "vendored-sources"\n\n[source.vendored-sources]\ndirectory = "/run/build/your-module/cargo/vendor"' > src-tauri/.cargo/config.toml
    - yarn install --offline --immutable --immutable-cache --inline-builds
    - yarn run tauri build -- -b deb
    - ar -x src-tauri/target/release/bundle/deb/\*.deb
    - tar -xf src-tauri/target/release/bundle/deb/your-app/data.tar.gz
    - install -Dm755 src-tauri/target/release/bundle/deb/your-app/data/usr/bin/your-command /app/bin/your-command
    - install -Dm644 src-tauri/target/release/bundle/deb/your-app/data/usr/share/applications/your-app.desktop /app/share/applications/org.your.id.desktop
    - install -Dm644 src-tauri/target/release/bundle/deb/your-app/data/usr/share/icons/hicolor/128x128/apps/your-app.png /app/share/icons/hicolor/128x128/apps/your-app.png
    - install -Dm644 src-tauri/target/release/bundle/deb/your-app/data/usr/share/icons/hicolor/32x32/apps/your-app.png /app/share/icons/hicolor/32x32/apps/your-app.png
    - install -Dm644 src-tauri/target/release/bundle/deb/your-app/data/usr/share/icons/hicolor/256x256@2/apps/your-app.png /app/share/icons/hicolor/512x512/apps/your-app.png
    - install -Dm644 src-tauri/target/release/bundle/deb/your-app/data/usr/share/icons/hicolor/scalable/apps/your-app.svg /app/share/icons/hicolor/scalable/apps/your-app.svg


    - install -Dm644 src-tauri/target/release/bundle/deb/your-app/data/usr/share/metainfo/org.your.id /app/share/metainfo/org.your.id
  ```
 ## Submitting To Flathub **_1. Fork The [Flathub Repository](https://github.com/flathub/flathub/fork)_** **_2. Clone the Fork_** 
  ```shell
  git clone --branch=new-pr git@github.com:your_github_username/flathub.git
  ```
 **_3. Enter the repository_** 
  ```shell
  cd flathub
  ```
 **_4. Create a new branch_** 
  ```shell
  git checkout -b your_app_name
  ```
 **_5. Open a pull request against the `new-pr` branch on github_** **_6. Your app will now enter the review process in which you may be asked to make changes to your project._** * Closed Source 
  ```sh
  # Generate your Node Sources
  flatpak-node-generator --no-requests-cache -o node-sources.json yarn /path/to/your/lock/file/yarn.lock


  # Generate your cargo sources


  python3 flatpak-builder-tools/cargo/flatpak-cargo-generator.py -o cargo-sources.json src-tauri/Cargo.lock
  ```
 * Yarn 
  ```sh
  # Generate your Node Sources
  flatpak-node-generator --no-requests-cache -o node-sources.json npm /path/to/your/lock/file/package-lock.json


  # Generate your cargo sources
  python3 flatpak-builder-tools/cargo/flatpak-cargo-generator.py -o cargo-sources.json src-tauri/Cargo.lock
  ```
 * NPM For detailed information on how Flatpak works, you can read [Building your first Flatpak](https://docs.flatpak.org/en/latest/first-build.html) This guide assumes you want to distribute your Flatpak via [Flathub](https://flathub.org/), the most commonly used platform for Flatpak distribution. If you plan on using other platforms, please consult their documentation instead. ## Prerequisites To test your app inside the Flatpak runtime you can build the Flatpak locally first before uploading your app to Flathub. This can also be helpful if you want to quickly share development builds. **1. Install `flatpak` and `org.flatpak.Builder`** To build Flatpaks locally you need `flatpak` from your distribution’s package manager: * Debian 
    ```sh
    sudo apt install flatpak
    ```
 * Arch 
    ```sh
    sudo pacman -S --needed flatpak
    ```
 * Fedora 
    ```sh
    sudo dnf install flatpak
    ```
 * Gentoo 
    ```sh
    sudo emerge --ask sys-apps/flatpak
    ```
 Then install the Flatpak-packaged `flatpak-builder` from Flathub instead of your distribution’s native `flatpak-builder` package (it avoids distro packaging issues and includes `flatpak-builder-lint` for Flathub readiness checks): 
  ```shell
  flatpak install flathub org.flatpak.Builder
  ```
 **2. Install the Flatpak Runtime** 
  ```shell
  flatpak install flathub org.gnome.Platform//51 org.gnome.Sdk//51
  ```
 **3. [Build the .deb of your tauri-app](/reference/config/#bundleconfig)** **4. [Create an AppStream MetaInfo file](https://www.freedesktop.org/software/appstream/metainfocreator/#/guiapp)** **5. Create the flatpak manifest** flatpak-builder.yaml 
  ```yaml
  id: <identifier>


  runtime: org.gnome.Platform
  runtime-version: '51'
  sdk: org.gnome.Sdk


  command: <main_binary_name>
  finish-args:
    - --socket=wayland # Permission needed to show the window
    - --socket=fallback-x11 # Permission needed to show the window
    - --device=dri # OpenGL, not necessary for all projects
    - --share=ipc
    - --talk-name=org.kde.StatusNotifierWatcher # Optional: needed only if your app uses the tray icon
    - --filesystem=xdg-run/tray-icon:create # Optional: needed only if your app uses the tray icon - see an alternative way below
    # - --env=WEBKIT_DISABLE_COMPOSITING_MODE=1 # Optional: may solve some issues with black webviews on Wayland


  modules:
    - name: binary
      buildsystem: simple


      sources:
        # A reference to the previously generated flatpak metainfo file
        - type: file
          path: flatpak.metainfo.xml
        # If you use GitHub releases, you can target an existing remote file
        - type: file
          url: https://github.com/your_username/your_repository/releases/download/v1.0.1/yourapp_1.0.1_amd64.deb
          sha256: 08305b5521e2cf0622e084f2b8f7f31f8a989fc7f407a7050fa3649facd61469 # This is required if you are using a remote source
          only-arches: [x86_64] # This source is only used on x86_64 Computers
        # You can also use a local file for testing
        # - type: file
        #   path: yourapp_1.0.1_amd64.deb
      build-commands:
        - set -e


        # Extract the deb package
        - mkdir deb-extract
        - ar -x *.deb --output deb-extract
        - tar -C deb-extract -xf deb-extract/data.tar.gz


        # Copy binary
        - 'install -Dm755 deb-extract/usr/bin/<executable_name> /app/bin/<executable_name>'


        # If you bundle files with additional resources, you should copy them:
        - mkdir -p /app/lib/<product_name>
        - cp -r deb-extract/usr/lib/<product_name>/. /app/lib/<product_name>
        - find /app/lib/<product_name> -type f -exec chmod 644 {} \;


        # Copy desktop file + ensure the right icon is set
        - sed -i 's/^Icon=.*/Icon=<identifier>/' deb-extract/usr/share/applications/<product_name>.desktop
        - install -Dm644 deb-extract/usr/share/applications/<product_name>.desktop /app/share/applications/<identifier>.desktop


        # Copy icons
        - install -Dm644 deb-extract/usr/share/icons/hicolor/128x128/apps/<main_binary_name>.png /app/share/icons/hicolor/128x128/apps/<identifier>.png
        - install -Dm644 deb-extract/usr/share/icons/hicolor/32x32/apps/<main_binary_name>.png /app/share/icons/hicolor/32x32/apps/<identifier>.png
        - install -Dm644 deb-extract/usr/share/icons/hicolor/256x256@2/apps/<main_binary_name>.png /app/share/icons/hicolor/256x256@2/apps/<identifier>.png
        - install -Dm644 flatpak.metainfo.xml /app/share/metainfo/<identifier>.metainfo.xml
  ```
 The Gnome 51 runtime includes all dependencies of the standard Tauri app with their correct versions. Using tray-icon without changing the Flatpak manifest If you prefer not opening access from your app to $XDG_RUNTIME_DIR (where tray-icon is saved on linux), you can change the path tauri saves the tray image: 
  ```rust
  TrayIconBuilder::new()
    .icon(app.default_window_icon().unwrap().clone())
    .temp_dir_path(app.path().app_cache_dir().unwrap()) // will save to the cache folder ($XDG_CACHE_HOME) where the app already has permission
    .build()
    .unwrap();
  ```
 **5. Install, and Test the app** 
  ```shell
  # Install the flatpak
  flatpak run org.flatpak.Builder --force-clean --user --disable-cache --repo flatpak-repo flatpak flatpak-builder.yaml


  # Optional: check your manifest for Flathub readiness
  flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest flatpak-builder.yaml


  # Run it
  flatpak run <your flatpak id> # or via your desktop environment


  # Update it
  flatpak -y --user update <your flatpak id>
  ```
 ## Adding additional libraries If your final binary requires more libraries than the default tauri app, you need to add them in your flatpak manifest. There are two ways to do this. For fast local development, it may work to simply include the already built library file (`.so`) from your local system. However, this is not recommended for the final build of the flatpak, as your local library file is not built for the flatpak runtime environment. This can introduce various bugs that can be very hard to find. Therefore, it is recommended to build the library your program depends on from source inside the flatpak as a build step. ## Submitting to flathub **_1. Fork The [Flathub Repository](https://github.com/flathub/flathub/fork)_** **_2. Clone the Fork_** 
  ```shell
  git clone --branch=new-pr git@github.com:your_github_username/flathub.git
  ```
 **_3. Enter the repository_** 
  ```shell
  cd flathub
  ```
 **_4. Create a new branch_** 
  ```shell
  git checkout -b your_app_name
  ```
 **_5. Add your apps manifest to the branch. Commit your changes, and then push them._** **_6. Open a pull request against the `new-pr` branch on github_** **_7. Your app will now enter the review process in which you may be asked to make changes to your project._** When your pull request is approved then you will receive an invitation to edit your apps repository. From here on you can update your app continuously. You can read more about this [in the flatpak documentation](https://docs.flatpak.org/en/latest/dependencies.html#bundling) * Debian 
  ```sh
  sudo apt install flatpak
  ```
 * Arch 
  ```sh
  sudo pacman -S --needed flatpak
  ```
 * Fedora 
  ```sh
  sudo dnf install flatpak
  ```
 * Gentoo 
  ```sh
  sudo emerge --ask sys-apps/flatpak
  ```

# Google Play

Google Play is the Android app distribution service maintained by Google. This guide covers the requirements for publishing your Android app on Google Play. Note Tauri uses an Android Studio project under the hood, so any official practice for building and publishing Android apps also apply to your app. See the [official documentation](https://developer.android.com/distribute) for more information. ## Requirements To distribute Android apps in the Play Store you must create a [Play Console](https://play.google.com/console/developers) developer account. Additionally, you must setup [code signing](/distribute/sign/android/). See the [release checklist](https://play.google.com/console/about/guides/releasewithconfidence/) for more information. ## Changing App Icon After running `tauri android init` to setup the Android Studio project, you can use the `tauri icon` command to update the app icons. * npm 
  ```sh
  npm run tauri icon /path/to/app-icon.png
  ```
 * yarn 
  ```sh
  yarn tauri icon /path/to/app-icon.png
  ```
 * pnpm 
  ```sh
  pnpm tauri icon /path/to/app-icon.png
  ```
 * deno 
  ```sh
  deno task tauri icon /path/to/app-icon.png
  ```
 * bun 
  ```sh
  bun tauri icon /path/to/app-icon.png
  ```
 * cargo 
  ```sh
  cargo tauri icon /path/to/app-icon.png
  ```
 ## Setting up Once you’ve created a Play Console developer account, you need to register your app on the Google [Play Console](https://play.google.com/console/developers) website. It will guide you through all the required forms and setup tasks. ## Build You can build an Android App Bundle (AAB) to upload to Google Play by running the following command: * npm 
  ```sh
  npm run tauri android build -- --aab
  ```
 * yarn 
  ```sh
  yarn tauri android build --aab
  ```
 * pnpm 
  ```sh
  pnpm tauri android build --aab
  ```
 * deno 
  ```sh
  deno task tauri android build --aab
  ```
 * bun 
  ```sh
  bun tauri android build --aab
  ```
 * cargo 
  ```sh
  cargo tauri android build --aab
  ```
 Tauri derives the version code from the value defined in [`tauri.conf.json > version`](/reference/config/#version) (`versionCode = major*1000000 + minor*1000 + patch`). You can set a custom version code in the \[`tauri.conf.json > bundle > android > versionCode`] configuration if you need a different version code scheme e.g. sequential codes: tauri.conf.json 
```diff
{
  "bundle": {
    "android": {
      +"versionCode": 100
    }
  }
}
```
 ### Build APKs The AAB format is the recommended bundle file to upload to Google Play, but it is also possible to generate APKs that can be used for testing or distribution outside the store. To compile APKs for your app you can use the `--apk` argument: * npm 
  ```sh
  npm run tauri android build -- --apk
  ```
 * yarn 
  ```sh
  yarn tauri android build --apk
  ```
 * pnpm 
  ```sh
  pnpm tauri android build --apk
  ```
 * deno 
  ```sh
  deno task tauri android build --apk
  ```
 * bun 
  ```sh
  bun tauri android build --apk
  ```
 * cargo 
  ```sh
  cargo tauri android build --apk
  ```
 ### Architecture selection By default Tauri builds your app for all supported architectures (aarch64, armv7, i686 and x86_64). To only compile for a subset of targets, you can use the `--target` argument: * npm 
  ```sh
  npm run tauri android build -- --aab --target aarch64 --target armv7
  ```
 * yarn 
  ```sh
  yarn tauri android build --aab --target aarch64 --target armv7
  ```
 * pnpm 
  ```sh
  pnpm tauri android build --aab --target aarch64 --target armv7
  ```
 * deno 
  ```sh
  deno task tauri android build --aab --target aarch64 --target armv7
  ```
 * bun 
  ```sh
  bun tauri android build --aab --target aarch64 --target armv7
  ```
 * cargo 
  ```sh
  cargo tauri android build --aab --target aarch64 --target armv7
  ```
 ### Separate bundles per architecture By default the generated AAB and APK is universal, containing all supported targets. To generate individual bundles per target, use the `--split-per-abi` argument. Note This is only useful for testing or distribution outside Google Play, as it reduces the file size but is less convenient to upload. Google Play handles the supported architectures for you. * npm 
  ```sh
  npm run tauri android build -- --apk --split-per-abi
  ```
 * yarn 
  ```sh
  yarn tauri android build --apk --split-per-abi
  ```
 * pnpm 
  ```sh
  pnpm tauri android build --apk --split-per-abi
  ```
 * deno 
  ```sh
  deno task tauri android build --apk --split-per-abi
  ```
 * bun 
  ```sh
  bun tauri android build --apk --split-per-abi
  ```
 * cargo 
  ```sh
  cargo tauri android build --apk --split-per-abi
  ```
 ### Changing the minimum supported Android version The minimum supported Android version for Tauri apps is Android 7.0 (codename Nougat, SDK 24). There are some techniques to use newer Android APIs while still supporting older systems. See the [Android documentation](https://developer.android.com/training/basics/supporting-devices/platforms#version-codes) for more information. If your app must execute on a newer Android version, you can configure \[`tauri.conf.json > bundle > android > minSdkVersion`]: tauri.conf.json 
```diff
{
  "bundle": {
    "android": {
      +"minSdkVersion": 28
    }
  }
}
```
 ## Upload After building your app and generating the Android App Bundle file, which can be found in `gen/android/app/build/outputs/bundle/universalRelease/app-universal-release.aab`, you can now create a new release and upload it in the Google Play Console. The first upload must be made manually in the website so it can verify your app signature and bundle identifier. Tauri currently does not offer a way to automate the process of creating Android releases, which must leverage the [Google Play Developer API](https://developers.google.com/android-publisher/api-ref/rest), but it is a work in progress.

# macOS Application Bundle

An application bundle is the package format that is executed on macOS. It is a simple directory that includes everything your application requires for successful operation, including your app executable, resources, the Info.plist file and other files such as macOS frameworks. To package your app as a macOS application bundle you can use the Tauri CLI and run the `tauri build` command in a Mac computer: * npm 
  ```sh
  npm run tauri build -- --bundles app
  ```
 * yarn 
  ```sh
  yarn tauri build --bundles app
  ```
 * pnpm 
  ```sh
  pnpm tauri build --bundles app
  ```
 * deno 
  ```sh
  deno task tauri build --bundles app
  ```
 * bun 
  ```sh
  bun tauri build --bundles app
  ```
 * cargo 
  ```sh
  cargo tauri build --bundles app
  ```
 Note GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri’s [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue. ## File structure The macOS app bundle is a directory with the following structure: 
```plaintext
├── <productName>.app
│   ├── Contents
│   │   ├── Info.plist
│   │   ├── ...additional files from [`tauri.conf.json > bundle > macOS > files`]
│   ├── MacOS
│   │   ├── <app-name> (app executable)
│   ├── Resources
│   │   ├── icon.icns (app icon)
│   │   ├── ...resources from [`tauri.conf.json > bundle > resources`]
│   ├── _CodeSignature (codesign information generated by Apple)
│   ├── Frameworks
│   ├── PlugIns
│   ├── SharedSupport
```
 See the [official documentation](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html) for more information. ## Native configuration The app bundle is configured by the `Info.plist` file, which includes key-value pairs with your app identity and configuration values read by macOS. Tauri automatically configures the most important properties such as your app binary name, version. bundle identifier, minimum system version and more. To extend the configuration file, create an `Info.plist` file in the `src-tauri` folder and include the key-pairs you desire: src-tauri/Info.plist 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>NSCameraUsageDescription</key>
  <string>Request camera access for WebRTC</string>
  <key>NSMicrophoneUsageDescription</key>
  <string>Request microphone access for WebRTC</string>
</dict>
</plist>
```
 This `Info.plist` file is merged with the values generated by the Tauri CLI. Be careful when overwriting default values such as application version as they might conflict with other configuration values and introduce unexpected behavior. See the [official Info.plist documentation](https://developer.apple.com/documentation/bundleresources/information_property_list) for more information. ### Info.plist localization The `Info.plist` file by itself only supports a single language, typically English. If you want to support multiple languages, you can create `InfoPlist.strings` files for each additional language. Each file belongs in its own language specific `lproj` directory in the `Resources` directory in the application bundle. To bundle these files automatically you can leverage Tauri’s [resources](/develop/resources/) feature. To do that, create a file structure in your project following this pattern: 
```plaintext
├── src-tauri
│   ├── tauri.conf.json
│   ├── infoplist
│   │   ├── de.lproj
│   │   │   ├── InfoPlist.strings
│   │   ├── fr.lproj
│   │   │   ├── InfoPlist.strings
```
 While the `infoplist` directory name can be chosen freely, as long as you update it in the resources config below, the `lproj` directories must follow the `<lang-code>.lproj` naming and the string catalogue files must be named `InfoPlist.strings` (capital i and p). For most cases the language code should be a two letter code following [BCP 47](https://www.rfc-editor.org/rfc/bcp/bcp47.txt). For the `Info.plist` example shown above, the `de.lproj > InfoPlist.strings` file could look like this: de.lproj/InfoPlist.strings 
```ini
NSCameraUsageDescription = "Kamera Zugriff wird benötigt für WebRTC Funktionalität";
NSMicrophoneUsageDescription = "Mikrofon Zugriff wird benötigt für WebRTC Funktionalität";
```
 Lastly, make Tauri pick up these files by using the resources feature mentioned above: src-tauri/tauri.conf.json 
```json
{
  "bundle": {
    "resources": {
      "infoplist/**": "./"
    }
  }
}
```
 ## Entitlements An entitlement is a special Apple configuration key-value pair that acts as a right or privilege that grants your app particular capabilities, such as act as the user’s default email client and using the App Sandbox feature. Entitlements are applied when your application is signed. See the [code signing documentation](/distribute/sign/macos/) for more information. To define the entitlements required by your application, you must create the entitlements file and configure Tauri to use it. 1. Create a `Entitlements.plist` file in the `src-tauri` folder and configure the key-value pairs you app requires: src-tauri/Entitlements.plist 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
</dict>
</plist>
```
 2. Configure Tauri to use the Entitlements.plist file: tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      +"entitlements": "./Entitlements.plist"
    }
  }
}
```
 See the [official documentation](https://developer.apple.com/documentation/bundleresources/entitlements) for more information. ## Minimum system version By default your Tauri application supports macOS 10.13 and above. If you are using an API that requires a newer macOS system and want to enforce that requirement in your app bundle, you can configure the [`tauri.conf.json > bundle > macOS > minimumSystemVersion`](/reference/config/#minimumsystemversion) value: tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      +"minimumSystemVersion": "12.0"
    }
  }
}
```
 ## Including macOS frameworks If your application requires additional macOS frameworks to run, you can list them in the [`tauri.conf.json > bundle > macOS > frameworks`](/reference/config/#frameworks-1) configuration. The frameworks list can include either system or custom frameworks and dylib files. tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      +"frameworks": [
        +"CoreAudio",
        +"./libs/libmsodbcsql.18.dylib",
        +"./frameworks/MyApp.framework"
+      ]
    }
  }
}
```
 Note * To reference a system framework you can just use its name (without the .framework extension) instead of absolute path * System frameworks must exist in either the `$HOME/Library/Frameworks`, `/Library/Frameworks/`, or `/Network/Library/Frameworks/` * To reference local frameworks and dylib files you must use the complete path to the framework, relative to the `src-tauri` directory ## Adding custom files You can use the [`tauri.conf.json > bundle > macOS > files`](/reference/config/#files-2) configuration to add custom files to your application bundle, which maps the destination path to its source relative to the `tauri.conf.json` file. The files are added to the `<product-name>.app/Contents` folder. tauri.conf.json 
```diff
{
  "bundle": {
    "macOS": {
      +"files": {
        +"embedded.provisionprofile": "./profile-name.provisionprofile",
        +"SharedSupport/docs.md": "./docs/index.md"
+      }
    }
  }
}
```
 In the above example, the `profile-name.provisionprofile` file is copied to `<product-name>.app/Contents/embedded.provisionprofile` and the `docs/index.md` file is copied to `<product-name>.app/Contents/SharedSupport/docs.md`.

# Microsoft Store

Microsoft Store is the Windows app store operated by Microsoft. This guide only covers details for distributing Windows Apps directly to the Microsoft Store. See the [Windows Installer guide](/distribute/windows-installer/) for more information on Windows installer distribution options and configurations. ## Requirements To publish apps on the Microsoft Store you must have a Microsoft account and [enroll](https://learn.microsoft.com/en-us/windows/apps/get-started/sign-up) as a developer either as an individual or as a company. ## Changing App Icon The Tauri CLI can generate all icons your app needs, including Microsoft Store icons. Use the `tauri icon` command to generate app icons from a single PNG or SVG source: * npm 
  ```sh
  npm run tauri icon /path/to/app-icon.png
  ```
 * yarn 
  ```sh
  yarn tauri icon /path/to/app-icon.png
  ```
 * pnpm 
  ```sh
  pnpm tauri icon /path/to/app-icon.png
  ```
 * deno 
  ```sh
  deno task tauri icon /path/to/app-icon.png
  ```
 * bun 
  ```sh
  bun tauri icon /path/to/app-icon.png
  ```
 * cargo 
  ```sh
  cargo tauri icon /path/to/app-icon.png
  ```
 ## Setting up After you have enrolled as a developer with your Microsoft account you need to register your app in the [Apps and Games](https://partner.microsoft.com/en-us/dashboard/apps-and-games/overview) page. Click `New Product`, select `EXE or MSI app` and reserve a unique name for your app. ## Build and upload Currently Tauri only generates [EXE and MSI](/distribute/windows-installer/) installers, so you must create a Microsoft Store application that only links to the unpacked application. The installer linked in the Microsoft Installer must be offline, [handle auto-updates](/plugin/updater/) and be [code signed](/distribute/sign/windows/). See the [official publish documentation](https://learn.microsoft.com/en-us/windows/apps/publish/) for more information. ### Offline Installer The Windows installer distributed through the Microsoft Store must use the [Offline Installer](/distribute/windows-installer/#offline-installer) Webview2 installation option. To only apply this installer configuration when bundling for Microsoft Store, you can define a separate Tauri configuration file: "src-tauri/tauri.microsoftstore.conf.json 
```json
{
  "bundle": {
    "windows": {
      "webviewInstallMode": {
        "type": "offlineInstaller"
      }
    }
  }
}
```
 Then merge that config file with the main one when bundling your Tauri app for Microsoft Store: * npm 
  ```sh
  npm run tauri build -- --no-bundle
  npm run tauri bundle -- --config src-tauri/tauri.microsoftstore.conf.json
  ```
 * yarn 
  ```sh
  yarn tauri build --no-bundle
  yarn tauri bundle --config src-tauri/tauri.microsoftstore.conf.json
  ```
 * pnpm 
  ```sh
  pnpm tauri build --no-bundle
  pnpm tauri bundle --config src-tauri/tauri.microsoftstore.conf.json
  ```
 * deno 
  ```sh
  deno task tauri build --no-bundle
  deno task tauri bundle --config src-tauri/tauri.microsoftstore.conf.json
  ```
 * bun 
  ```sh
  bun tauri build --no-bundle
  bun tauri bundle --config src-tauri/tauri.microsoftstore.conf.json
  ```
 * cargo 
  ```sh
  cargo tauri build --no-bundle
  cargo tauri bundle --config src-tauri/tauri.microsoftstore.conf.json
  ```
 This is particularly useful when setting up your CI/CD to upload your app to the Microsoft Store while having a separate configuration for the Windows installer you distribute outside the app store. ### Silent install The Microsoft Store requires Win32 installers to support silent installation. If your installer does not install silently, your submission is rejected with an error such as: 
```plaintext
10.2.9.2 Security - Package Submissions | Win32 products must install silently.
```
 When you register your installer in Partner Center you must provide the [silent install parameters](https://learn.microsoft.com/en-us/windows/uwp/publish/msiexe/provide-package-details) so the Store can run it unattended. Tauri’s NSIS `-setup.exe` installer installs silently with the `/S` flag (note the uppercase `S`): 
```plaintext
MyApp_x64-setup.exe /S
```
 Enter `/S` as the silent install argument in the installer parameters of your Microsoft Store product. If you distribute the MSI installer instead, use the standard `msiexec` flag `/quiet`. ### Publisher Your application [publisher](/reference/config/#publisher) name cannot match the application product name. If the publisher configuration value is not set, Tauri derives it from the second part of your bundle identifier. Since the publisher name cannot match the product name, the following configuration is invalid: tauri.conf.json 
```json
{
  "productName": "Example",
  "identifier": "com.example.app"
}
```
 In this case you can define the [publisher](/reference/config/#publisher) value separately to fix this conflict: tauri.conf.json 
```diff
{
  "productName": "Example",
  "identifier": "com.example.app",
  +"bundle": {
    +"publisher": "Example Inc."
+  }
}
```
 ### Upload After building the Windows installer for Microsoft Store, you can upload it to the distribution service of your choice and link it in your application page in the Microsoft Store website.

# CrabNebula Cloud

## Distributing with CrabNebula Cloud [CrabNebula](https://crabnebula.dev) is an official Tauri partner providing services and tooling for Tauri applications. The [CrabNebula Cloud](https://crabnebula.dev/cloud/) is a platform for application distribution that seamlessly integrates with the Tauri updater. The Cloud offers a Content Delivery Network (CDN) that is capable of shipping your application installers and updates globally while being cost effective and exposing download metrics. With the CrabNebula Cloud service it is simple to implement multiple release channels, download buttons for your application website and more. Setting up your Tauri app to use the Cloud is easy: all you need to do is to sign in to the [Cloud website](https://web.crabnebula.cloud/) using your GitHub account, create your organization and application and install its CLI to create a release and upload the Tauri bundles. Additionally, a [GitHub Action](https://github.com/crabnebula-dev/cloud-release/) is provided to simplify the process of using the CLI on GitHub workflows. For more information, see the [CrabNebula Cloud documentation](https://docs.crabnebula.dev/cloud/).

# GitHub

This guide will show you how to use [tauri-action](https://github.com/tauri-apps/tauri-action) in [GitHub Actions](https://docs.github.com/en/actions) to easily build and upload your app, and how to make Tauri’s updater query the newly created GitHub release for updates. Lastly, it will also show how to set up a more complicated build pipeline for Linux Arm AppImages. Code Signing To set up code signing for Windows and macOS in your workflow, follow the specific guide for each platform: * [Windows Code Signing](/distribute/sign/windows/) * [macOS Code Signing](/distribute/sign/macos/) If you build a macOS app without an Apple signing certificate, configure an [ad-hoc signing identity](/distribute/sign/macos/#ad-hoc-signing). This can avoid macOS treating Apple Silicon builds downloaded from GitHub releases as damaged. ## Getting Started To set up `tauri-action` you must first set up a GitHub repository. You can also use this action on a repository that does not have Tauri configured yet since it can automatically initialize Tauri for you, please see the [action’s readme](https://github.com/tauri-apps/tauri-action/#project-initialization) for necessary configuration options. Go to the Actions tab on your GitHub project page and select “New workflow”, then choose “Set up a workflow yourself”. Replace the file with the workflow from [below](#example-workflow) or from one of the [action’s examples](https://github.com/tauri-apps/tauri-action/tree/dev/examples). ## Configuration Please see the `tauri-action` [readme](https://github.com/tauri-apps/tauri-action/#inputs) for all available configuration options. When your app is not on the root of the repository, use the `projectPath` input. You may freely modify the workflow name, change its triggers, and add more steps such as `npm run lint` or `npm run test`. The important part is that you keep the below line at the end of the workflow since this runs the build script and releases your app. ### How to Trigger The release workflow shown below and in the `tauri-action` examples is triggered by pushed to the `release` branch. The action automatically creates a git tag and a title for the GitHub release using the application version. As another example, you can also change the trigger to run the workflow on the push of a version git tag such as `app-v0.7.0`: 
```yaml
name: 'publish'


on:
  push:
    tags:
      - 'app-v*'
```
 For a full list of possible trigger configurations, check out the official [GitHub documentation](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows). ## Example Workflow Below is an example workflow that has been set up to run every time you push to the `release` branch. This workflow will build and release your app for Windows x64, Linux x64, Linux Arm64, macOS x64 and macOS Arm64 (M1 and above). The steps this workflow takes are: 1. Checkout the repository using `actions/checkout@v7`. 2. Install Linux system dependencies required to build the app. 3. Set up Node.js LTS and a cache for global npm/yarn/pnpm package data using `actions/setup-node@v6`. 4. Set up Rust and a cache for Rust’s build artifacts using `dtolnay/rust-toolchain@stable` and `swatinem/rust-cache@v2`. 5. Install the frontend dependencies and, if not configured as [`beforeBuildCommand`](/reference/config/#beforebuildcommand), run the web app’s build script. 6. Lastly, it uses `tauri-apps/tauri-action@v1` to run `tauri build`, generate the artifacts, and create a GitHub release. 
```yaml
name: 'publish'


on:
  workflow_dispatch:
  push:
    branches:
      - release


jobs:
  publish-tauri:
    permissions:
      contents: write
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: 'macos-latest' # for Arm based macs (M1 and above).
            args: '--target aarch64-apple-darwin'
          - platform: 'macos-latest' # for Intel based macs.
            args: '--target x86_64-apple-darwin'
          - platform: 'ubuntu-22.04'
            args: ''
          - platform: 'ubuntu-22.04-arm' # Only available in public repos.
            args: ''
          - platform: 'windows-latest'
            args: ''


    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v7


      - name: install dependencies (ubuntu only)
        if: matrix.platform == 'ubuntu-22.04' || matrix.platform == 'ubuntu-22.04-arm' # This must match the platform value defined above.
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf xdg-utils


      - name: setup node
        uses: actions/setup-node@v6
        with:
          node-version: lts/*
          cache: 'npm' # Set this to npm, yarn or pnpm.


      - name: install Rust stable
        uses: dtolnay/rust-toolchain@stable
        with:
          # Those targets are only used on macos runners so it's in an `if` to slightly speed up windows and linux builds.
          targets: ${{ matrix.platform == 'macos-latest' && 'aarch64-apple-darwin,x86_64-apple-darwin' || '' }}


      - name: Rust cache
        uses: swatinem/rust-cache@v2
        with:
          # This matches tauri's default project layout. Change this if you have a different layout.
          workspaces: './src-tauri -> target'


      - name: install frontend dependencies
        # If you don't have `beforeBuildCommand` configured you may want to build your frontend here too.
        run: npm install # change this to npm, yarn or pnpm depending on which one you use.


      - uses: tauri-apps/tauri-action@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tagName: app-v__VERSION__ # the action automatically replaces __VERSION__ with the app version.
          releaseName: 'App v__VERSION__'
          releaseBody: 'See the assets to download this version and install.'
          releaseDraft: true
          prerelease: false
          args: ${{ matrix.args }}
```
 For more configuration options, check out the [`tauri-action`](https://github.com/tauri-apps/tauri-action) repository and its [examples](https://github.com/tauri-apps/tauri-action/blob/dev/examples/). Caution Carefully read through the [Usage limits, billing, and administration](https://docs.github.com/en/actions/learn-github-actions/usage-limits-billing-and-administration) documentation for GitHub Actions. ## Arm Runner Compilation August 2025 Update Github has [released](https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/#get-started) publicly available `ubuntu-22.04-arm` and `ubuntu-24.04-arm` runners. You can use these to build your app for Arm64 in public repos with the workflow example above. This workflow uses [`pguyot/arm-runner-action`](https://github.com/pguyot/arm-runner-action) to compile directly on an emulated Arm runner. This bridges the gap for missing cross-architecture build support in the AppImage tooling. Danger `arm-runner-action` is **much** slower than GitHub’s standard runners, so be careful in private repositories where you’re invoiced for build minutes. An uncached build for a fresh `create-tauri-app` project needs \~1 hour. 
```yaml
name: 'Publish Linux Arm builds'


on:
  workflow_dispatch:
  push:
    branches:
      - release


jobs:
  build:
    runs-on: ubuntu-22.04


    strategy:
      matrix:
        arch: [aarch64, armv7l]
        include:
          - arch: aarch64
            cpu: cortex-a72
            base_image: https://dietpi.com/downloads/images/DietPi_RPi5-ARMv8-Bookworm.img.xz
            deb: arm64
            rpm: aarch64
            appimage: aarch64
          - arch: armv7l
            cpu: cortex-a53
            deb: armhfp
            rpm: arm
            appimage: armhf
            base_image: https://dietpi.com/downloads/images/DietPi_RPi-ARMv7-Bookworm.img.xz


    steps:
      - uses: actions/checkout@v3


      - name: Cache rust build artifacts
        uses: Swatinem/rust-cache@v2
        with:
          workspaces: src-tauri
          cache-on-failure: true


      - name: Build app
        uses: pguyot/arm-runner-action@v2.6.5
        with:
          base_image: ${{ matrix.base_image }}
          cpu: ${{ matrix.cpu }}
          bind_mount_repository: true
          image_additional_mb: 10240
          optimize_image: no
          #exit_on_fail: no
          commands: |
            # Prevent Rust from complaining about $HOME not matching eid home
            export HOME=/root


            # Workaround to CI worker being stuck on Updating crates.io index
            export CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse


            # Install setup prerequisites
            apt-get update -y --allow-releaseinfo-change
            apt-get autoremove -y
            apt-get install -y --no-install-recommends --no-install-suggests curl libwebkit2gtk-4.1-dev build-essential libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev patchelf libfuse2 file
            curl https://sh.rustup.rs -sSf | sh -s -- -y
            . "$HOME/.cargo/env"
            curl -fsSL https://deb.nodesource.com/setup_lts.x | bash
            apt-get install -y nodejs


            # Install frontend dependencies
            npm install


            # Build the application
            npm run tauri build -- --verbose


      - name: Get app version
        run: echo "APP_VERSION=$(jq -r .version src-tauri/tauri.conf.json)" >> $GITHUB_ENV


      # TODO: Combine this with the basic workflow and upload the files to the Release.
      - name: Upload deb bundle
        uses: actions/upload-artifact@v3
        with:
          name: Debian Bundle
          path: ${{ github.workspace }}/src-tauri/target/release/bundle/deb/appname_${{ env.APP_VERSION }}_${{ matrix.deb }}.deb


      - name: Upload rpm bundle
        uses: actions/upload-artifact@v3
        with:
          name: RPM Bundle
          path: ${{ github.workspace }}/src-tauri/target/release/bundle/rpm/appname-${{ env.APP_VERSION }}-1.${{ matrix.rpm }}.rpm


      - name: Upload appimage bundle
        uses: actions/upload-artifact@v3
        with:
          name: AppImage Bundle
          path: ${{ github.workspace }}/src-tauri/target/release/bundle/appimage/appname_${{ env.APP_VERSION }}_${{ matrix.appimage }}.AppImage
```
 ## Troubleshooting ### GitHub Environment Token The GitHub Token is automatically issued by GitHub for each workflow run without further configuration, which means there is no risk of secret leakage. This token however only has read permissions by default and you may get a “Resource not accessible by integration” error when running the workflow. If this happens, you may need to add write permissions to this token. To do this, go to your GitHub project settings, select `Actions`, scroll down to `Workflow permissions`, and check “Read and write permissions”. You can see the GitHub Token being passed to the workflow via this line in the workflow: 
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

# RPM

Note Some sections in this guide are optional. This includes configuring scripts and certain other steps. Feel free to adapt the instructions based on your specific needs and requirements. This guide covers how to distribute and manage RPM packages, including retrieving package information, configuring scripts, setting dependencies, and signing packages. Note GUI apps on macOS and Linux do not inherit the `$PATH` from your shell dotfiles (`.bashrc`, `.bash_profile`, `.zshrc`, etc). Check out Tauri’s [fix-path-env-rs](https://github.com/tauri-apps/fix-path-env-rs) crate to fix this issue. ## Limitations Core libraries such as glibc frequently break compatibility with older systems. For this reason, you must build your Tauri application using the oldest base system you intend to support that also provides Tauri v2’s required WebKitGTK 4.1 packages. Ubuntu 22.04 and Debian 12 are suitable baseline examples because they provide `libwebkit2gtk-4.1-dev` from their standard package repositories. Building on a newer base system can raise the minimum glibc version required by your app, so when running on an older system, you may face a runtime error like `/usr/lib/libc.so.6: version 'GLIBC_2.33' not found`. We recommend using a Docker container or GitHub Actions to build your Tauri application for Linux. See the issues [tauri-apps/tauri#1355](https://github.com/tauri-apps/tauri/issues/1355) and [rust-lang/rust#57497](https://github.com/rust-lang/rust/issues/57497), in addition to the [AppImage guide](https://docs.appimage.org/reference/best-practices.html#binaries-compiled-on-old-enough-base-system) for more information. ## Configuring the RPM package Tauri allows you to configure the RPM package by adding scripts, setting dependencies, adding a license, including custom files, and more. For detailed information about configurable options, please refer to: [RpmConfig](/reference/config/#rpmconfig). ### Add post, pre-install/remove script to the package The RPM package manager allows you to run scripts before or after the installation or removal of the package. For example, you can use these scripts to start a service after the package is installed. Here’s an example of how to add these scripts: 1. Create a folder named `scripts` in the `src-tauri` directory in your project. 
```bash
mkdir src-tauri/scripts
```
 2. Create the script files in the folder. 
```bash
touch src-tauri/scripts/postinstall.sh \
touch src-tauri/scripts/preinstall.sh \
touch src-tauri/scripts/preremove.sh \
touch src-tauri/scripts/postremove.sh
```
 Now if we look inside `/src-tauri/scripts` we will see: 
```bash
ls src-tauri/scripts/
postinstall.sh  postremove.sh  preinstall.sh  preremove.sh
```
 3. Add some content to the scripts preinstall.sh 
```bash
echo "-------------"
echo "This is pre"
echo "Install Value: $1"
echo "Upgrade Value: $1"
echo "Uninstall Value: $1"
echo "-------------"
```
 postinstall.sh 
```bash
echo "-------------"
echo "This is post"
echo "Install Value: $1"
echo "Upgrade Value: $1"
echo "Uninstall Value: $1"
echo "-------------"
```
 preremove.sh 
```bash
echo "-------------"
echo "This is preun"
echo "Install Value: $1"
echo "Upgrade Value: $1"
echo "Uninstall Value: $1"
echo "-------------"
```
 postremove.sh 
```bash
echo "-------------"
echo "This is postun"
echo "Install Value: $1"
echo "Upgrade Value: $1"
echo "Uninstall Value: $1"
echo "-------------"
```
 4. Add the scripts to the`tauri.conf.json` file tauri.conf.json 
```json
{
  "bundle": {
    "linux": {
      "rpm": {
        "epoch": 0,
        "files": {},
        "release": "1",
        // add the script here
        "preInstallScript": "/path/to/your/project/src-tauri/scripts/prescript.sh",
        "postInstallScript": "/path/to/your/project/src-tauri/scripts/postscript.sh",
        "preRemoveScript": "/path/to/your/project/src-tauri/scripts/prescript.sh",
        "postRemoveScript": "/path/to/your/project/src-tauri/scripts/postscript.sh"
      }
    }
  }
}
```
 ### Setting the Conflict, Provides, Depends, Files, Obsoletes, DesktopTemplate, and Epoch * **conflict**: Prevents the installation of the package if it conflicts with another package. For example, if you update an RPM package that your app depends on and the new version is incompatible with your app. * **provides**: Lists the RPM dependencies that your application provides. * **depends**: Lists the RPM dependencies that your application needs to run. * **files**: Specifies which files to include in the package. * **obsoletes**: Lists the RPM dependencies that your application obsoletes. Note If this package is installed, packages listed as “obsoletes” will be automatically removed if present. * **desktopTemplate**: Adds a custom desktop file to the package. * **epoch**: Defines weighted dependencies based on version numbers. Caution It is not recommended to use epoch unless necessary, as it alters how the package manager compares package versions. For more information about epoch, please check: [RPM Packaging Guide](https://rpm-packaging-guide.github.io/#epoch-scriptlets-and-triggers). To use these options, add the following to your `tauri.conf.json` : tauri.conf.json 
```json
{
  "bundle": {
    "linux": {
      "rpm": {
        "postRemoveScript": "/path/to/your/project/src-tauri/scripts/postscript.sh",
        "conflicts": ["oldLib.rpm"],
        "depends": ["newLib.rpm"],
        "obsoletes": ["veryoldLib.rpm"],
        "provides": ["coolLib.rpm"],
        "desktopTemplate": "/path/to/your/project/src-tauri/desktop-template.desktop"
      }
    }
  }
}
```
 ### Add a license to the package To add a license to the package, add the following to the `src-tauri/cargo.toml` or in the `src-tauri/tauri.conf.json` file: src-tauri/cargo.toml 
```toml
[package]
name = "tauri-app"
version = "0.0.0"
description = "A Tauri App"
authors = ["you"]
edition = "2021"
license = "MIT" # add the license here
# ...  rest of the file
```
 And for `src-tauri/tauri.conf.json` src-tauri/tauri.conf.json 
```json
{
  "bundle": {
    "licenseFile": "../LICENSE", // put the path to the license file here
    "license": "MIT" // add the license here
  }
}
```
 ## Building the RPM package To build the RPM package, you can use the following command: * npm 
  ```sh
  npm run tauri build
  ```
 * yarn 
  ```sh
  yarn tauri build
  ```
 * pnpm 
  ```sh
  pnpm tauri build
  ```
 * deno 
  ```sh
  deno task tauri build
  ```
 * bun 
  ```sh
  bun tauri build
  ```
 * cargo 
  ```sh
  cargo tauri build
  ```
 This command will build the RPM package in the `src-tauri/target/release/bundle/rpm` directory. ## Signing the RPM package Tauri allows you to sign the package with the key you have in your system during the build process. To do this, you will need to generate a GPG key. #### Generate a GPG key To generate a GPG key you can use the following command: 
```bash
gpg --gen-key
```
 Follow the instruction to generate the key. Once the key is generated, you will need to add it to your environment variable. You can do this by adding the following to your .bashrc or .zshrc file or just export it in the terminal: 
```bash
export TAURI_SIGNING_RPM_KEY=$(cat /home/johndoe/my_super_private.key)
```
 If you have a passphrase for the key, you can add it to the environment variable: 
```bash
export TAURI_SIGNING_RPM_KEY_PASSPHRASE=password
```
 Now you can build the package with the following command: * npm 
  ```sh
  npm run tauri build
  ```
 * yarn 
  ```sh
  yarn tauri build
  ```
 * pnpm 
  ```sh
  pnpm tauri build
  ```
 * deno 
  ```sh
  deno task tauri build
  ```
 * bun 
  ```sh
  bun tauri build
  ```
 * cargo 
  ```sh
  cargo tauri build
  ```
 ### Verify the signature Note This should be done only to test the signature locally. Before verifying the signature, you will need to create and import the public key to the RPM database: 
```bash
gpg --export -a 'Tauri-App' > RPM-GPG-KEY-Tauri-App
```
 
```bash
sudo rpm --import RPM-GPG-KEY-Tauri-App
```
 Now that the key is imported, we have to edit the `~/.rpmmacros` file to utilize the key. \~/.rpmmacros 
```bash
%_signature gpg
%_gpg_path /home/johndoe/.gnupg
%_gpg_name Tauri-App
%_gpgbin /usr/bin/gpg2
%__gpg_sign_cmd %{__gpg} \
    gpg --force-v3-sigs --digest-algo=sha1 --batch --no-verbose --no-armor \
    --passphrase-fd 3 --no-secmem-warning -u "%{_gpg_name}" \
    -sbo %{__signature_filename} %{__plaintext_filename}
```
 Finally, you can verify the package using the following command: 
```bash
rpm  -v --checksig tauri-app-0.0.0-1.x86_64.rpm
```
 ## Debugging the RPM package In this section, we will see how to debug the RPM package by checking the content of the package and getting information about the package. ### Getting information about the package To get information about your package, such as the version, release, and architecture, use the following command: 
```bash
rpm -qip package_name.rpm
```
 ### Query specific information about the package For example, if you want to get the name, version, release, architecture, and size of the package, use the following command: 
```bash
rpm  -qp --queryformat '[%{NAME} %{VERSION} %{RELEASE} %{ARCH} %{SIZE}\n]' package_name.rpm
```
 Note *`--queryformat`* is a format string that can be used to get specific information about the package. The information that can be retrieved is from the rpm -qip command. ### Checking the content of the package To check the content of the package, use the following command: 
```bash
rpm -qlp package_name.rpm
```
 This command will list all the files that are included in the package. ### Debugging scripts To debug post/pre-install/remove scripts, use the following command: 
```bash
rpm -qp --scripts package_name.rpm
```
 This command will print the content of the scripts. ### Checking dependencies To check the dependencies of the package, use the following command: 
```bash
rpm -qp --requires package_name.rpm
```
 ### List packages that depend on a specific package To list the packages that depend on a specific package, use the following command: 
```bash
rpm -q --whatrequires package_name.rpm
```
 ### Debugging Installation Issues If you encounter issues during the installation of an RPM package, you can use the `-vv` (very verbose) option to get detailed output: 
```bash
rpm -ivvh package_name.rpm
```
 Or for an already installed package: 
```bash
rpm -Uvvh package_name.rpm
```
 ## Cross-Compiling for ARM-based Devices This guide covers manual compilation. Check out our [GitHub Action guide](/distribute/pipelines/github/#arm-runner-compilation) for an example workflow that leverages QEMU to build the app. This will be much slower but will also be able to build AppImages. Manual compilation is suitable when you don’t need to compile your application frequently and prefer a one-time setup. The following steps expect you to use a Linux distribution based on Debian/Ubuntu. 1. #### Install Rust targets for your desired architecture * For ARMv7 (32-bit): `rustup target add armv7-unknown-linux-gnueabihf` * For ARMv8 (ARM64, 64-bit): `rustup target add aarch64-unknown-linux-gnu` 2. #### Install the corresponding linker for your chosen architecture * For ARMv7: `sudo apt install gcc-arm-linux-gnueabihf` * For ARMv8 (ARM64): `sudo apt install gcc-aarch64-linux-gnu` 3. #### Open or create the file `<project-root>/.cargo/config.toml` and add the following configurations accordingly 
   ```toml
   [target.armv7-unknown-linux-gnueabihf]
   linker = "arm-linux-gnueabihf-gcc"


   [target.aarch64-unknown-linux-gnu]
   linker = "aarch64-linux-gnu-gcc"
   ```
 4. #### Enable the respective architecture in the package manager * For ARMv7: `sudo dpkg --add-architecture armhf` * For ARMv8 (ARM64): `sudo dpkg --add-architecture arm64` 5. #### Adjusting Package Sources On Debian, this step should not be necessary, but on other distributions, you might need to edit /etc/apt/sources.list to include the ARM architecture variant. For example on Ubuntu 22.04 add these lines to the bottom of the file (Remember to replace jammy with the codename of your Ubuntu version): 
   ```plaintext
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-backports main restricted universe multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security multiverse
   ```
 Then, to prevent issues with the main packages, you have to add the correct main architecture to all other lines the file contained beforehand. For standard 64-bit systems you need to add \[arch=amd64], the full file on Ubuntu 22.04 then looks similar to this: Show solution 
   ```plaintext
   # See http://help.ubuntu.com/community/UpgradeNotes for how to upgrade to
   # newer versions of the distribution.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy main restricted
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy main restricted


   ## Major bug fix updates produced after the final release of the
   ## distribution.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-updates main restricted


   ## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
   ## team. Also, please note that software in universe WILL NOT receive any
   ## review or updates from the Ubuntu security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy universe
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy universe
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates universe
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-updates universe


   ## N.B. software from this repository is ENTIRELY UNSUPPORTED by the Ubuntu
   ## team, and may not be under a free licence. Please satisfy yourself as to
   ## your rights to use the software. Also, please note that software in
   ## multiverse WILL NOT receive any review or updates from the Ubuntu
   ## security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy multiverse
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy multiverse
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-updates multiverse


   ## N.B. software from this repository may not have been tested as
   ## extensively as that contained in the main release, although it includes
   ## newer versions of some applications which may provide useful features.
   ## Also, please note that software in backports WILL NOT receive any review
   ## or updates from the Ubuntu security team.
   deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ jammy-backports main restricted universe multiverse
   # deb-src http://archive.ubuntu.com/ubuntu/ jammy-backports main restricted universe multiverse


   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security main restricted
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security main restricted
   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security universe
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security universe
   deb [arch=amd64] http://security.ubuntu.com/ubuntu/ jammy-security multiverse
   # deb-src http://security.ubuntu.com/ubuntu/ jammy-security multiverse


   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-updates multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-backports main restricted universe multiverse
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security main restricted
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security universe
   deb [arch=armhf,arm64] http://ports.ubuntu.com/ubuntu-ports jammy-security multiverse
   ```
 6. #### Update the package information: `sudo apt-get update && sudo apt-get upgrade -y` 7. #### Install the required webkitgtk library for your chosen architecture * For ARMv7: `sudo apt install libwebkit2gtk-4.1-dev:armhf` * For ARMv8 (ARM64): `sudo apt install libwebkit2gtk-4.1-dev:arm64` 8. #### Install OpenSSL or use a vendored version This is not always required so you may want to proceed first and check if you see errors like `Failed to find OpenSSL development headers`. * Either install the development headers system-wide: * For ARMv7: `sudo apt install libssl-dev:armhf` * For ARMv8 (ARM64): `sudo apt install libssl-dev:arm64` * Or enable the vendor feature for the OpenSSL Rust crate which will affect all other Rust dependencies using the same minor version. You can do so by adding this to the dependencies section in your `Cargo.toml` file: 
   ```toml
   openssl-sys = {version = "0.9", features = ["vendored"]}
   ```
 9. #### Set the `PKG_CONFIG_SYSROOT_DIR` to the appropriate directory based on your chosen architecture * For ARMv7: `export PKG_CONFIG_SYSROOT_DIR=/usr/arm-linux-gnueabihf/` * For ARMv8 (ARM64): `export PKG_CONFIG_SYSROOT_DIR=/usr/aarch64-linux-gnu/` 10. #### Build the app for your desired ARM version * For ARMv7: cargo tauri build –target armv7-unknown-linux-gnueabihf * For ARMv8 (ARM64): cargo tauri build –target aarch64-unknown-linux-gnu Choose the appropriate set of instructions based on whether you want to cross-compile your Tauri application for ARMv7 or ARMv8 (ARM64). Please note that the specific steps may vary depending on your Linux distribution and setup.

# Android Code Signing

To publish on the Play Store, you need to sign your app with a digital certificate. Android App Bundles and APKs must be signed before being uploaded for distribution. Google also provides an additional signing mechanism for Android App Bundles distributed in the Play Store. See the [official Play App Signing documentation](https://support.google.com/googleplay/android-developer/answer/9842756?hl=en\&visit_id=638549803861403647-3347771264\&rd=1) for more information. ## Creating a keystore and upload key Android signing requires a Java Keystore file that can be generated using the official `keytool` CLI: * macOS/Linux 
  ```plaintext
  keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
  ```
 * Windows 
  ```plaintext
  keytool -genkey -v -keystore $env:USERPROFILE\upload-keystore.jks -storetype JKS -keyalg RSA -keysize 2048 -validity 10000 -alias upload
  ```
 This command stores the `upload-keystore.jks` file in your home directory. If you want to store it elsewhere, change the argument you pass to the `-keystore` parameter. Security Warning Keep the `keystore` file private; don’t check it into public source control! See the [official documentation](https://developer.android.com/studio/publish/app-signing#generate-key) for more information. ## Configure the signing key Create a file named `[project]/src-tauri/gen/android/keystore.properties` that contains a reference to your keystore: 
```plaintext
password=<password defined when keytool was executed>
keyAlias=upload
storeFile=<location of the key store file, such as /Users/<user name>/upload-keystore.jks or C:\\Users\\<user name>\\upload-keystore.jks>
```
 Security Warning Keep the `keystore.properties` file private; don’t check it into public source control. You will usually generate this file in your CI/CD platform. The following snippet contains an example job step for GitHub Actions: 
```yml
- name: setup Android signing
  run: |
    cd src-tauri/gen/android
    echo "keyAlias=${{ secrets.ANDROID_KEY_ALIAS }}" > keystore.properties
    echo "password=${{ secrets.ANDROID_KEY_PASSWORD }}" >> keystore.properties
    base64 -d <<< "${{ secrets.ANDROID_KEY_BASE64 }}" > $RUNNER_TEMP/keystore.jks
    echo "storeFile=$RUNNER_TEMP/keystore.jks" >> keystore.properties
```
 In this example the keystore was exported to base64 with `base64 -i /path/to/keystore.jks` and set as the `ANDROID_KEY_BASE64` secret. ### Configure Gradle to use the signing key Configure gradle to use your upload key when building your app in release mode by editing the `[project]/src-tauri/gen/android/app/build.gradle.kts` file. 1. Add the needed import at the beginning of the file: 
   ```kotlin
   import java.io.FileInputStream
   ```
 2. Add the `release` signing config before the `buildTypes` block: 
   ```kotlin
   signingConfigs {
       create("release") {
           val keystorePropertiesFile = rootProject.file("keystore.properties")
           val keystoreProperties = Properties()
           if (keystorePropertiesFile.exists()) {
               keystoreProperties.load(FileInputStream(keystorePropertiesFile))
           }


           keyAlias = keystoreProperties["keyAlias"] as String
           keyPassword = keystoreProperties["password"] as String
           storeFile = file(keystoreProperties["storeFile"] as String)
           storePassword = keystoreProperties["password"] as String
       }
   }


   buildTypes {
       ...
   }
   ```
 3. Use the new `release` signing config in the `release` config in `buildTypes` block: 
   ```kotlin
   buildTypes {
       getByName("release") {
           signingConfig = signingConfigs.getByName("release")
       }
   }
   ```
 Release builds of your app will now be signed automatically.

# iOS Code Signing

Code signing on iOS is required to distribute your application through the official [Apple App Store](https://www.apple.com/app-store/) or possibly alternative marketplaces in the European Union and in general to install and execute on end user devices. ## Prerequisites Code signing on iOS requires enrolling to the [Apple Developer](https://developer.apple.com) program, which at the time of writing costs 99$ per year. You also need an Apple device where you perform the code signing. This is required by the signing process and due to Apple’s Terms and Conditions. To distribute iOS applications you must have your bundle identifier registered in the App Store Connect, an appropriate iOS code signing certificate and a mobile provisioning profile that links them together and enables the iOS capabilities used by your app. These requirements can be either automatically managed by Xcode or provided manually. ## Automatic Signing Letting Xcode manage the signing and provisioning for your app is the most convenient way to export your iOS app to be distributed. It automatically registers your bundle identifier, manages iOS capabilities changes, and configures an appropriate certificate based on your export method. Automatic signing is enabled by default, and uses the account configured in Xcode to authenticate when used on your local machine.\ To register your account, open the Xcode application and open the Settings page in the `Xcode > Settings` menu, switch to the Accounts tab and click the `+` icon. To use the automatic signing in CI/CD platforms you must create an App Store Connect API key and define the `APPLE_API_ISSUER`, `APPLE_API_KEY` and `APPLE_API_KEY_PATH` environment variables.\ Open the [App Store Connect’s Users and Access page](https://appstoreconnect.apple.com/access/users), select the Integrations tab, click on the Add button and select a name and the Admin access. The `APPLE_API_ISSUER` (Issuer ID) is presented above the keys table, and the `APPLE_API_KEY` is the value on the Key ID column on that table. You also need to download the private key, which can only be done once and is only visible after a page reload (the button is shown on the table row for the newly created key). The private key file path must be set via the `APPLE_API_KEY_PATH` environment variable. ## Manual Signing To manually sign your iOS app you can provide the certificate and mobile provisioning profile via environment variables: * **IOS_CERTIFICATE**: base64 representation of the certificate exported from the Keychain. * **IOS_CERTIFICATE_PASSWORD**: password of the certificate set when exporting it from the Keychain. * **IOS_MOBILE_PROVISION**: base64 representation of the provisioning profile. The following sections explain how to get these values. ### Signing Certificate After enrolling, navigate to the [Certificates](https://developer.apple.com/account/resources/certificates/list) page to create a new Apple Distribution certificate. Download the new certificate and install it to the macOS Keychain. To export the certificate key, open the “Keychain Access” app, expand the certificate’s entry, right-click on the key item and select “Export \<key-name>” item. Select the path of the exported .p12 file and remember its password. Run the following `base64` command to convert the certificate to base64 and copy it to the clipboard: 
```plaintext
base64 -i <path-to-certificate.p12> | pbcopy
```
 The value in the clipboard is now the base64 representation of the signing certificate. Save it and use it as the `IOS_CERTIFICATE` environment variable value. The certificate password must be set to the `IOS_CERTIFICATE_PASSWORD` variable. ### Provisioning Profile Additionally, you must provide the provisioning profile for your application. In the [Identifiers](https://developer.apple.com/account/resources/identifiers/list) page, create a new App ID and make sure its “Bundle ID” value matches the identifier set in the [`identifier`](/reference/config/#identifier) configuration. Navigate to the [Profiles](https://developer.apple.com/account/resources/profiles/list) page to create a new provisioning profile. For App Store distribution, it must be an “App Store Connect” profile. Select the appropriate App ID and link the certificate you previously created. After creating the provisioning profile, download it and run the following `base64` command to convert the profile and copy it to the clipboard: 
```plaintext
base64 -i <path-to-profile.mobileprovision> | pbcopy
```
 The value in the clipboard is now the base64 representation of the provisioning profile. Save it and use it as the `IOS_MOBILE_PROVISION` environment variable value. Now you can build your iOS application and distribute on the App Store!

# Linux Code Signing

This guide provides information on code signing for Linux packages. While artifact signing is not required for your application to be deployed on Linux, it can be used to increase trust into your deployed application. Signing the binaries allows your end user to verify that these are genuine and have not been modified by another untrusted entity. ## Signing for AppImages The AppImage can be signed using either gpg or gpg2. ### Prerequisites A key for signing must be prepared. A new one can be generated using: 
```shell
gpg2 --full-gen-key
```
 Please refer to the gpg or gpg2 documentation for additional information. You should take additional care to back up your private and public keys in a secure location. ### Signing You can embed a signature in the AppImage by setting the following environment variables: * **SIGN**: set to `1` to sign the AppImage. * **SIGN_KEY**: optional variable to use a specific GPG Key ID for signing. * **APPIMAGETOOL_SIGN_PASSPHRASE**: the signing key password. If unset, gpg shows a dialog so you can input it. You must set this when building in CI/CD platforms. * **APPIMAGETOOL_FORCE_SIGN**: by default the AppImage is generated even if signing fails. To exit on errors, you can set this variable to `1`. You can display the signature embedded in the AppImage by running the following command: 
```shell
./src-tauri/target/release/bundle/appimage/$APPNAME_$VERSION_amd64.AppImage --appimage-signature
```
 Note that you need to change the $APPNAME and $VERSION values with the correct ones based on your configuration. Caution **The signature is not verified** AppImage does not validate the signature, so you can’t rely on it to check whether the file has been tampered with or not. The user must manually verify the signature using the AppImage validate tool. This requires you to publish your key ID on an authenticated channel (e.g. your website served via TLS), so the end user can view and verify. See [the official AppImage documentation](https://docs.appimage.org/packaging-guide/optional/signatures.html) for additional information. ### Validate the signature The AppImage validate tool can be downloaded from [here](https://github.com/AppImageCommunity/AppImageUpdate/releases/tag/continuous). Select one of the `validate-$PLATFORM.AppImage` files. Run the following command to validate the signature: 
```shell
chmod +x validate-$PLATFORM.AppImage
./validate-$PLATFORM.AppImage $TAURI_OUTPUT.AppImage
```
 If the signature is valid, the output will be: 
```plaintext
Validation result: validation successful
Signatures found with key fingerprints: $KEY_ID
====================
Validator report:
Signature checked for key with fingerprint $KEY_ID:
Validation successful
```

# macOS Code Signing

Code signing is required on macOS to allow your application to be listed in the [Apple App Store](https://www.apple.com/app-store/) and to prevent a warning that your application is broken and can not be started, when downloaded from the browser. ## Prerequisites Code signing on macOS requires an [Apple Developer](https://developer.apple.com) account which is either paid (99$ per year) or on the free plan (only for testing and development purposes). You also need an Apple device where you perform the code signing. This is required by the signing process and due to Apple’s Terms and Conditions. Note Note when using a free Apple Developer account, you will not be able to notarize your application and it will still show up as not verified when opening the app. ## Signing To setup code signing for macOS you must create an Apple code signing certificate and install it to your Mac computer keychain or export it to be used in CI/CD platforms. ### Creating a signing certificate To create a new signing certificate, you must generate a Certificate Signing Request (CSR) file from your Mac computer. See [creating a certificate signing request](https://developer.apple.com/help/account/create-certificates/create-a-certificate-signing-request) to learn how to create the CSR for code signing. On your Apple Developer account, navigate to the [Certificates, IDs & Profiles page](https://developer.apple.com/account/resources/certificates/list) and click on the `Create a certificate` button to open the interface to create a new certificate. Choose the appropriate certificate type (`Apple Distribution` to submit apps to the App Store, and `Developer ID Application` to ship apps outside the App Store). Upload your CSR, and the certificate will be created. Note Only the Apple Developer `Account Holder` can create *Developer ID Application* certificates. But it can be associated with a different Apple ID by creating a CSR with a different user email address. ### Downloading the certificate On the [Certificates, IDs & Profiles page](https://developer.apple.com/account/resources/certificates/list), click on the certificate you want to use and click on the `Download` button. It saves a `.cer` file that installs the certificate on the keychain once opened. ### Configuring Tauri You can configure Tauri to use your certificate when building macOS apps on your local machine or when using CI/CD platforms. #### Signing locally With the certificate installed in your Mac computer keychain, you can configure Tauri to use it for code signing. The name of the certificate’s keychain entry represents the `signing identity`, which can also be found by executing: 
```sh
security find-identity -v -p codesigning
```
 This identity can be provided in the [`tauri.conf.json > bundle > macOS > signingIdentity`](/reference/config/#signingidentity) configuration option or via the `APPLE_SIGNING_IDENTITY` environment variable. Note A signing certificate is only valid if associated with your Apple ID. An invalid certificate won’t be listed on the *Keychain Access > My Certificates* tab or the *security find-identity -v -p codesigning* output. If the certificate does not download to the correct location, make sure the “login” option is selected in *Keychain Access* under “Default Keychains” when downloading the .cer file. #### Signing in CI/CD platforms To use the certificate in CI/CD platforms, you must export the certificate to a base64 string and configure the `APPLE_CERTIFICATE` and `APPLE_CERTIFICATE_PASSWORD` environment variables: 1. Open the `Keychain Access` app, click the *My Certificates* tab in the *login* keychain and find your certificate’s entry. 2. Expand the entry, right-click on the key item, and select `Export "$KEYNAME"`. 3. Select the path to save the certificate’s `.p12` file and define a password for the exported certificate. 4. Convert the `.p12` file to base64 running the following script on the terminal: 
```sh
openssl base64 -A -in /path/to/certificate.p12 -out certificate-base64.txt
```
 5. Set the contents of the `certificate-base64.txt` file to the `APPLE_CERTIFICATE` environment variable. 6. Set the certificate password to the `APPLE_CERTIFICATE_PASSWORD` environment variable. ## Notarization To notarize your application, you must provide credentials for Tauri to authenticate with Apple. This can be done via the App Store Connect API, or via your Apple ID. * App Store Connect 1. Open the [App Store Connect’s Users and Access page](https://appstoreconnect.apple.com/access/users), select the Integrations tab, click on the Add button and select a name and the Developer access. 2. Set the `APPLE_API_ISSUER` environment variable to the value presented above the keys table. 3. Set the `APPLE_API_KEY` environment variable to the value on the Key ID column on that table. 4. Download the private key, which can only be done once and is only visible after a page reload (the button is shown on the table row for the newly created key). 5. Set the `APPLE_API_KEY_PATH` environment variable to the file path of the downloaded private key. * Apple ID 1. Set the `APPLE_ID` environment variable to your Apple account email. 2. Set the `APPLE_PASSWORD` environment variable to an [app-specific password](https://support.apple.com/en-ca/HT204397) for your Apple account. 3. Set the `APPLE_TEAM_ID` environment variable to your Apple Team ID. You can find your Team ID in [your account’s membership page](https://developer.apple.com/account#MembershipDetailsCard). After setting these environment variables, rerun your Tauri build or bundle command. For example, to build a DMG with pnpm, run `pnpm tauri build --bundles dmg` again. If you need to skip stapling for an initial notarization pass, append `--skip-stapling` directly to the Tauri command, such as `pnpm tauri build --bundles dmg --skip-stapling`. Note Notarization is required when using a *Developer ID Application* certificate. ## Ad-Hoc Signing If you do not wish to provide an Apple-authenticated identity, but still wish to sign your application, you can configure an *ad-hoc* signature. This is useful on ARM (Apple Silicon) devices, where code-signing is required for all apps from the Internet. Caution Ad-hoc code signing does not prevent MacOS from requiring users to [whitelist the installation in their Privacy & Security settings](https://support.apple.com/guide/mac-help/open-a-mac-app-from-an-unknown-developer-mh40616/mac). To configure an ad-hoc signature, provide the pseudo-identity `-` to Tauri, e.g. 
```json
"signingIdentity": "-"
```
 For details on configuring Tauri’s signing identity, see [above](#configuring-tauri).

# Windows Code Signing

Code signing is required on Windows to allow your application to be listed in the [Microsoft Store](https://apps.microsoft.com/) and to prevent a [SmartScreen](https://en.wikipedia.org/wiki/Microsoft_SmartScreen) warning that your application is not trusted and can not be started, when downloaded from the browser. It is not required to execute your application on Windows, as long as your end user is okay with ignoring the [SmartScreen](https://en.wikipedia.org/wiki/Microsoft_SmartScreen) warning or your user does not download via the browser. The exception is Windows 11 with [Smart App Control](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/overview) turned on: it blocks unknown unsigned apps even if they weren’t downloaded from the browser, and users can’t allow a single app, only turn Smart App Control off entirely. This guide covers signing via OV (Organization Validated) certificates and Azure Key Vault. If you use any other signing mechanism not documented here, such as EV (Extended Validation) certificates, check out your certificate issuer documentation and refer to the [custom sign command](#custom-sign-command) section. ## OV Certificates Danger This guide only applies to OV code signing certificates acquired before June 1st 2023! For code signing with EV certificates and OV certificates received after that date please consult the documentation of your certificate issuer instead. Note Since 2024, an EV Certificate no longer gives your app an immediate reputation with Microsoft SmartScreen. Microsoft removed the special treatment of EV code signing certificates from its Trusted Root Program in 2024, so EV and OV certificates now build SmartScreen reputation the same way, and a newly signed release can show a warning with either. See Microsoft’s [SmartScreen reputation for Windows app developers](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation) and [Current status of Windows app distribution features](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/distribution-feature-status#smartscreen-reputation-ev-certificates-no-longer-grant-instant-bypass). An OV Certificate is generally cheaper and available to individuals. With either kind of certificate, Microsoft SmartScreen may show a warning to users when they download the app until the file and the certificate build enough reputation. Signing every release with the same certificate lets that reputation carry across releases. You may opt for [submitting your app](https://www.microsoft.com/en-us/wdsi/filesubmission/) to Microsoft for manual review. Although not guaranteed, if the app does not contain any malicious code, Microsoft may grant additional reputation and potentially remove the warning for that specific uploaded file. See the [comparison](https://www.digicert.com/difference-between-dv-ov-and-ev-ssl-certificates) to learn more about OV vs EV certificates. ### Prerequisites * Windows - you can likely use other platforms, but this tutorial uses Powershell native features. * A working Tauri application * Code signing certificate - you can acquire one of these on services listed in [Microsoft’s docs](https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/code-signing-cert-manage). There are likely additional authorities for non-EV certificates than included in that list, please compare them yourself and choose one at your own risk. * Please make sure to get a **code signing** certificate, SSL certificates do not work! ### Getting Started There are a few things we have to do to get Windows prepared for code signing. This includes converting our certificate to a specific format, installing this certificate, and decoding the required information from the certificate. 1. #### Convert your `.cer` to `.pfx` * You will need the following: * certificate file (mine is `cert.cer`) * private key file (mine is `private-key.key`) * Open up a command prompt and change to your current directory using `cd Documents/Certs` * Convert your `.cer` to a `.pfx` using `openssl pkcs12 -export -in cert.cer -inkey private-key.key -out certificate.pfx` * You should be prompted to enter an export password **DON’T FORGET IT!** 2. #### Import your `.pfx` file into the keystore. * We now need to import our `.pfx` file. * Assign your export password to a variable using `$WINDOWS_PFX_PASSWORD = 'MYPASSWORD'` * Now Import the certificate using `Import-PfxCertificate -FilePath certificate.pfx -CertStoreLocation Cert:\CurrentUser\My -Password (ConvertTo-SecureString -String $WINDOWS_PFX_PASSWORD -Force -AsPlainText)` 3. #### Prepare Variables * Start ➡️ `certmgr.msc` to open Personal Certificate Management, then open Personal/Certificates. * Find the certificate we just imported and double-click on it, then click on the Details tab. * The Signature hash algorithm will be our `digestAlgorithm`. (Hint: this is likely `sha256`) * Scroll down to Thumbprint. There should be a value like `A1B1A2B2A3B3A4B4A5B5A6B6A7B7A8B8A9B9A0B0`. This is our `certificateThumbprint`. * We also need a timestamp URL; this is a time server used to verify the time of the certificate signing. I’m using `http://timestamp.comodoca.com`, but whoever you got your certificate from likely has one as well. ### Prepare `tauri.conf.json` file 1. Now that we have our `certificateThumbprint`, `digestAlgorithm`, & `timestampUrl` we will open up the `tauri.conf.json`. 2. In the `tauri.conf.json` you will look for the `tauri` -> `bundle` -> `windows` section. There are three variables for the information we have captured. Fill it out like below. 
```json
"windows": {
        "certificateThumbprint": "A1B1A2B2A3B3A4B4A5B5A6B6A7B7A8B8A9B9A0B0",
        "digestAlgorithm": "sha256",
        "timestampUrl": "http://timestamp.comodoca.com"
}
```
 3. Save and run `tauri build` 4. In the console output, you should see the following output. 
```plaintext
info: signing app
info: running signtool "C:\\Program Files (x86)\\Windows Kits\\10\\bin\\10.0.19041.0\\x64\\signtool.exe"
info: "Done Adding Additional Store\r\nSuccessfully signed: APPLICATION FILE PATH HERE
```
 Which shows you have successfully signed the `.exe`. And that’s it! You have successfully set up your Tauri application for Windows signing. ### Sign your application with GitHub Actions. We can also create a workflow to sign the application with GitHub actions. #### GitHub Secrets We need to add a few GitHub secrets for the proper configuration of the GitHub Action. These can be named however you would like. * You can view the [encrypted secrets](https://docs.github.com/en/actions/reference/encrypted-secrets) guide on how to add GitHub secrets. The secrets we used are as follows | GitHub Secrets | Value for Variable | | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | | WINDOWS_CERTIFICATE | Base64 encoded version of your .pfx certificate, can be done using this command `certutil -encode certificate.pfx base64cert.txt` | | WINDOWS_CERTIFICATE_PASSWORD | Certificate export password used on creation of certificate .pfx | #### Workflow Modifications 1. We need to add a step in the workflow to import the certificate into the Windows environment. This workflow accomplishes the following 1. Assign GitHub secrets to environment variables 2. Create a new `certificate` directory 3. Import `WINDOWS_CERTIFICATE` into tempCert.txt 4. Use `certutil` to decode the tempCert.txt from base64 into a `.pfx` file. 5. Remove tempCert.txt 6. Import the `.pfx` file into the Cert store of Windows & convert the `WINDOWS_CERTIFICATE_PASSWORD` to a secure string to be used in the import command. 2. We will be using the [`tauri-action` publish template](https://github.com/tauri-apps/tauri-action). 
```yml
name: 'publish'
on:
  push:
    branches:
      - release


jobs:
  publish-tauri:
    strategy:
      fail-fast: false
      matrix:
        platform: [macos-latest, ubuntu-latest, windows-latest]


    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v2
      - name: setup node
        uses: actions/setup-node@v1
        with:
          node-version: 12
      - name: install Rust stable
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - name: install webkit2gtk (ubuntu only)
        if: matrix.platform == 'ubuntu-latest'
        run: |
          sudo apt-get update
          sudo apt-get install -y webkit2gtk-4.0
      - name: install app dependencies and build it
        run: yarn && yarn build
      - uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tagName: app-v__VERSION__ # the action automatically replaces \_\_VERSION\_\_ with the app version
          releaseName: 'App v__VERSION__'
          releaseBody: 'See the assets to download this version and install.'
          releaseDraft: true
          prerelease: false
```
 3. Right above `-name: install app dependencies and build it` you will want to add the following step 
```yml
- name: import windows certificate
  if: matrix.platform == 'windows-latest'
  env:
    WINDOWS_CERTIFICATE: ${{ secrets.WINDOWS_CERTIFICATE }}
    WINDOWS_CERTIFICATE_PASSWORD: ${{ secrets.WINDOWS_CERTIFICATE_PASSWORD }}
  run: |
    New-Item -ItemType directory -Path certificate
    Set-Content -Path certificate/tempCert.txt -Value $env:WINDOWS_CERTIFICATE
    certutil -decode certificate/tempCert.txt certificate/certificate.pfx
    Remove-Item -path certificate -include tempCert.txt
    Import-PfxCertificate -FilePath certificate/certificate.pfx -CertStoreLocation Cert:\CurrentUser\My -Password (ConvertTo-SecureString -String $env:WINDOWS_CERTIFICATE_PASSWORD -Force -AsPlainText)
```
 4. Save and push to your repo. 5. Your workflow can now import your windows certificate and import it into the GitHub runner, allowing for automated code signing! ## Azure Key Vault You can sign the Windows executables by providing an Azure Key Vault certificate and credentials. Note This guide uses [relic](https://github.com/sassoftware/relic) due to its support to secret-based authentication, though you can configure alternative tools if you prefer. To download relic, check its [releases page](https://github.com/sassoftware/relic/releases/) or run `go install github.com/sassoftware/relic/v8@latest`. 1. Key Vault In the [Azure Portal](https://portal.azure.com) navigate to the [Key vaults service](https://portal.azure.com/#browse/Microsoft.KeyVault%2Fvaults) to create a new key vault by clicking the “Create” button. Remember the “Key vault name” as you will need that information to configure the certificate URL. 2. Certificate After creating a key vault, select it and go to the “Objects > Certificates” page to create a new certificate and click the “Generate/Import” button. Remember the “Certificate name” as you will need that information to configure the certificate URL. 3. Tauri Configuration [relic](https://github.com/sassoftware/relic) uses a configuration file to determine which signing key it should use. For Azure Key Vault you also need the certificate URL. Create a `relic.conf` file in the `src-tauri` folder and configure relic to use your certificate: src-tauri/relic.conf 
```yml
tokens:
  azure:
    type: azure


keys:
  azure:
    token: azure
    id: https://\<KEY_VAULT_NAME\>.vault.azure.net/certificates/\<CERTIFICATE_NAME\>
```
 Note that you must replace \<KEY_VAULT_NAME> and \<CERTIFICATE_NAME> with the appropriate names from the previous steps. To configure Tauri to use your Azure Key Vault configuration for signing change the [bundle > windows > signCommand](/reference/config/#signcommand) config value: tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "signCommand": "relic sign --file %1 --key azure --config relic.conf"
    }
  }
}
```
 4. Credentials [relic](https://github.com/sassoftware/relic) must authenticate with Azure in order to load the certificate. In the Azure portal landing page, go to the “Microsoft Entra ID” service and head to the “Manage > App registrations” page. Click “New registration” to create a new app. After creating the app, you are redirected to the application details page where you can see the “Application (client) ID” and “Directory (tenant) ID” values. Set these IDs to the `AZURE_CLIENT_ID` and `AZURE_TENANT_ID` environment variables respectively. In the “Manage > Certificates & secrets” page click the “New client secret” button and set the text in the “Value” column as the `AZURE_CLIENT_SECRET` environment variable. After setting up all the credentials, head back to your key vault’s page and navigate to the “Access control (IAM)” page. You must assign the “Key Vault Certificate User” and “Key Vault Crypto User” roles to your newly created application. After setting up all these variables, running `tauri build` will produce signed Windows installers! ## Custom Sign Command In the [Azure Key Vault](#azure-key-vault) documentation above we used a powerful Tauri Windows signing configuration to force the Tauri CLI to use a special shell command to sign Windows installer executables. The [bundle > windows > signCommand](/reference/config/#signcommand) configuration option can be used to use any codesign tool that can sign Windows executables. ## Azure Artifact Signing You can sign the Windows executables by providing an Azure Artifact Signing (previously called Azure Code Signing/Azure Trusted Signing) certificate and credentials. If you don’t have an Azure Artifact signing Account yet you can follow this [tutorial](https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/). ### Prerequisites If you want to sign with Github Actions everything should be installed. 1. [Artifact Signing Account](https://learn.microsoft.com/en-us/azure/trusted-signing/quickstart?tabs=registerrp-portal,account-portal,certificateprofile-portal,deleteresources-portal) and permissions configured 2. [.NET](https://dotnet.microsoft.com/en-us/download/dotnet/8.0) (.NET 8 recommended) 3. [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?tabs=azure-cli#install-or-update) 4. [Signtool](https://learn.microsoft.com/en-us/dotnet/framework/tools/signtool-exe) (Windows 11 SDK 10.0.26100.0 or later recommended) ### Getting Started You need to install [artifact-signing-cli](https://github.com/Levminer/artifact-signing-cli) and configure your environment variables. 1. #### Install artifact-signing-cli * `cargo install artifact-signing-cli` 2. #### Configure environment variables * artifact-signing-cli needs the following environment variables to be set, don’t forget to add these as Github Actions [secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions): * `AZURE_CLIENT_ID`: The client ID of your [App Registration](https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/#step-4-create-app-registration-user-credentials) * `AZURE_CLIENT_SECRET`: The client secret of [App Registration](https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/#step-4-create-app-registration-user-credentials) * `AZURE_TENANT_ID`: The tenant ID of your Azure directory, you can also get this from your [App Registration](https://melatonin.dev/blog/code-signing-on-windows-with-azure-trusted-signing/#step-4-create-app-registration-user-credentials) 3. ### Modify your `tauri.conf.json` file * You can modify your `tauri.conf.json` or you can create a specific config file for Windows. Replace the URL and the certificate name with your own values. * -e: The endpoint of your Azure Artifact Signing account * -a: The name of your Azure Artifact Signing Account * -c: The name of your Certificate profile inside your Azure Artifact Signing Account * -d: The description of the signed content (optional). When signing a .msi installer, this description will appear as the installer’s name in the UAC prompt or will be a random string of characters if unset. tauri.conf.json 
   ```json
   {
     "bundle": {
       "windows": {
         "signCommand": "artifact-signing-cli -e https://wus2.codesigning.azure.net -a MyAccount -c MyProfile -d MyApp %1"
       }
     }
   }
   ```

# Snapcraft

## Prerequisites **1. Install `snap`** * Debian 
  ```shell
  sudo apt install snapd
  ```
 * Arch 
  ```shell
  sudo pacman -S --needed git base-devel
  git clone https://aur.archlinux.org/snapd.git
  cd snapd
  makepkg -si
  sudo systemctl enable --now snapd.socket
  sudo systemctl start snapd.socket
  sudo systemctl enable --now snapd.apparmor.service
  ```
 * Fedora 
  ```shell
  sudo dnf install snapd
  # Enable classic snap support
  sudo ln -s /var/lib/snapd/snap /snap
  ```
 Reboot your system afterwards. **2. Install a base snap** 
```shell
sudo snap install core22
```
 **3. Install `snapcraft`** 
```shell
sudo snap install snapcraft --classic
```
 ## Configuration 1. Create an UbuntuOne account. 2. Go to the [Snapcraft](https://snapcraft.io) website and register an App name. 3. Create a snapcraft.yaml file in your projects root. 4. Adjust the names in the snapcraft.yaml file. 
```yaml
name: appname
base: core22
version: '0.1.0'
summary: Your summary # 79 char long summary
description: |
  Your description


grade: stable
confinement: strict


layout:
  /usr/lib/$SNAPCRAFT_ARCH_TRIPLET/webkit2gtk-4.1:
    bind: $SNAP/usr/lib/$SNAPCRAFT_ARCH_TRIPLET/webkit2gtk-4.1


apps:
  appname:
    command: usr/bin/appname
    desktop: usr/share/applications/appname.desktop
    extensions: [gnome]
    #plugs:
    #  - network
    # Add whatever plugs you need here, see https://snapcraft.io/docs/snapcraft-interfaces for more info.
    # The gnome extension already includes [ desktop, desktop-legacy, gsettings, opengl, wayland, x11, mount-observe, calendar-service ]
    #  - single-instance-plug # add this if you're using the single-instance plugin
    #slots:
    # Add the slots you need to expose to other snaps
    #  - single-instance-plug # add this if you're using the single-instance plugin


# Add these lines only if you're using the single-instance plugin
# Check https://v2.tauri.app/plugin/single-instance/ for details
#slots:
#  single-instance:
#    interface: dbus
#    bus: session
#    name: org.net_mydomain_MyApp.SingleInstance # Remember to change net_mydomain_MyApp to your app ID with "_" instead of "." and "-"
#
#plugs:
#  single-instance-plug:
#    interface: dbus
#    bus: session
#    name: org.net_mydomain_MyApp.SingleInstance # Remember to change net_mydomain_MyApp to your app ID with "_" instead of "." and "-"


package-repositories:
  - type: apt
    components: [main]
    suites: [noble]
    key-id: 78E1918602959B9C59103100F1831DDAFC42E99D
    url: http://ppa.launchpad.net/snappy-dev/snapcraft-daily/ubuntu


parts:
  build-app:
    plugin: dump
    build-snaps:
      - node/20/stable
      - rustup/latest/stable
    build-packages:
      - libwebkit2gtk-4.1-dev
      - build-essential
      - curl
      - wget
      - file
      - libxdo-dev
      - libssl-dev
      - libayatana-appindicator3-dev
      - librsvg2-dev
      - dpkg
    stage-packages:
      - libwebkit2gtk-4.1-0
      - libayatana-appindicator3-1
    source: .
    override-build: |
      set -eu
      npm install
      npm run tauri build -- --bundles deb
      dpkg -x src-tauri/target/release/bundle/deb/*.deb $SNAPCRAFT_PART_INSTALL/
      sed -i -e "s|Icon=appname|Icon=/usr/share/icons/hicolor/32x32/apps/appname.png|g" $SNAPCRAFT_PART_INSTALL/usr/share/applications/appname.desktop
```
 ### Explanation * The `name` variable defines the name of your app and is required to be set to the name that you have registered earlier. * The `base` variable defines which core you are using. * The `version` variable defines the version, and should be updated with each change to the source repository. * The `apps` section allows you to expose the desktop and binary files to allow the user to run your app. * The `package-repositories` section allows you to add a package repository to help you satisfy your dependencies. * `build-packages`/`build-snaps` defines the build dependencies for your snap. * `stage-packages`/`stage-snaps` defines the runtime dependencies for your snap. * The `override-build` section runs a series of commands after the sources were pulled. ## Building 
```sh
sudo snapcraft
```
 ## Testing 
```shell
snap run your-app
```
 ## Releasing Manually 
```shell
snapcraft login # Login with your UbuntuOne credentials
snapcraft upload --release=stable mysnap_latest_amd64.snap
```
 ## Building automatically 1. On your apps developer page click on the `builds` tab. 2. Click `login with github`. 3. Enter in your repository’s details.

# Windows Installer

Tauri applications for Windows are either distributed as Microsoft Installers (`.msi` files) using the [WiX Toolset v3](https://wixtoolset.org/documentation/manual/v3/) or as setup executables (`-setup.exe` files) using [NSIS](https://nsis.sourceforge.io/Main_Page). Please note that `.msi` installers can **only be created on Windows** as WiX can only run on Windows systems. Cross-compilation for NSIS installers is shown below. This guide provides information about available customization options for the installer. ## Building To build and bundle your app into a Windows installer you can use the Tauri CLI and run the `tauri build` command in a Windows computer: * npm 
  ```sh
  npm run tauri build
  ```
 * yarn 
  ```sh
  yarn tauri build
  ```
 * pnpm 
  ```sh
  pnpm tauri build
  ```
 * deno 
  ```sh
  deno task tauri build
  ```
 * bun 
  ```sh
  bun tauri build
  ```
 * cargo 
  ```sh
  cargo tauri build
  ```
 VBSCRIPT requirement for MSI packages Building MSI packages (`"targets": "msi"` or `"targets": "all"` in `tauri.conf.json`) requires the VBSCRIPT optional feature to be enabled on Windows. This feature is enabled by default on most Windows installations, but if you encounter errors like `failed to run light.exe`, you may need to enable it manually through **Settings** → **Apps** → **Optional features** → **More Windows features**. See the [Prerequisites guide](/start/prerequisites/#vbscript-for-msi-installers) for detailed instructions. ### Build Windows apps on Linux and macOS Cross compiling Windows apps on Linux and macOS hosts is possible with caveats when using [NSIS](https://nsis.sourceforge.io/Main_Page). It is not as straight forward as compiling on Windows directly and is not tested as much. Therefore it should only be used as a last resort if local VMs or CI solutions like GitHub Actions don’t work for you. Note Signing cross compiled Windows installers requires an external signing tool. See the [signing documentation](/distribute/sign/windows/) for more information. Since Tauri officially only supports the MSVC Windows target, the setup is a bit more involved. #### Install NSIS * Linux Some Linux distributions have NSIS available in their repositories, for example on Ubuntu you can install NSIS by running this command: Ubuntu 
  ```sh
  sudo apt install nsis
  ```
 But on many other distributions you have to compile NSIS yourself or download Stubs and Plugins manually that weren’t included in the distro’s binary package. Fedora for example only provides the binary but not the Stubs and Plugins: Fedora 
  ```sh
  sudo dnf in mingw64-nsis
  wget https://github.com/tauri-apps/binary-releases/releases/download/nsis-3/nsis-3.zip
  unzip nsis-3.zip
  sudo cp nsis-3.08/Stubs/* /usr/share/nsis/Stubs/
  sudo cp -r nsis-3.08/Plugins/** /usr/share/nsis/Plugins/
  ```
 * macOS On macOS you will need \[Homebrew] to install NSIS: macOS 
  ```sh
  brew install nsis
  ```
 #### Install LLVM and the LLD Linker Since the default Microsoft linker only works on Windows we will also need to install a new linker. To compile the Windows Resource file which is used for setting the app icon among other things we will also need the `llvm-rc` binary which is part of the LLVM project. * Linux Ubuntu 
  ```sh
  sudo apt install lld llvm
  ```
 On Linux you also need to install the `clang` package if you added dependencies that compile C/C++ dependencies as part of their build scripts. Default Tauri apps should not require this. * macOS macOS 
  ```sh
  brew install llvm
  ```
 On macOS you also have to add `/opt/homebrew/opt/llvm/bin` to your `$PATH` as suggested in the install output. #### Install the Windows Rust target Assuming you’re building for 64-bit Windows systems: 
```sh
rustup target add x86_64-pc-windows-msvc
```
 #### Install `cargo-xwin` Instead of setting the Windows SDKs up manually we will use \[`cargo-xwin`] as Tauri’s “runner”: 
```sh
cargo install --locked cargo-xwin
```
 By default `cargo-xwin` will download the Windows SDKs into a project-local folder. If you have multiple projects and want to share those files you can set the `XWIN_CACHE_DIR` environment variable with a path to the preferred location. #### Building the App Now it should be as simple as adding the runner and target to the `tauri build` command: * npm 
  ```sh
  npm run tauri build -- --runner cargo-xwin --target x86_64-pc-windows-msvc
  ```
 * yarn 
  ```sh
  yarn tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc
  ```
 * pnpm 
  ```sh
  pnpm tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc
  ```
 * deno 
  ```sh
  deno task tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc
  ```
 * bun 
  ```sh
  bun tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc
  ```
 * cargo 
  ```sh
  cargo tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc
  ```
 The build output will then be in `target/x86_64-pc-windows-msvc/release/bundle/nsis/`. ### Building for 32-bit or ARM The Tauri CLI compiles your executable using your machine’s architecture by default. Assuming that you’re developing on a 64-bit machine, the CLI will produce 64-bit applications. If you need to support **32-bit** machines, you can compile your application with a **different** [Rust target](https://doc.rust-lang.org/nightly/rustc/platform-support.html) using the `--target` flag: * npm 
  ```sh
  npm run tauri build -- --target i686-pc-windows-msvc
  ```
 * yarn 
  ```sh
  yarn tauri build --target i686-pc-windows-msvc
  ```
 * pnpm 
  ```sh
  pnpm tauri build --target i686-pc-windows-msvc
  ```
 * deno 
  ```sh
  deno task tauri build --target i686-pc-windows-msvc
  ```
 * bun 
  ```sh
  bun tauri build --target i686-pc-windows-msvc
  ```
 * cargo 
  ```sh
  cargo tauri build --target i686-pc-windows-msvc
  ```
 By default, Rust only installs toolchains for your machine’s target, so you need to install the 32-bit Windows toolchain first: `rustup target add i686-pc-windows-msvc`. If you need to build for **ARM64** you first need to install additional build tools. To do this, open `Visual Studio Installer`, click on “Modify”, and in the “Individual Components” tab install the “C++ ARM64 build tools”. At the time of writing, the exact name in VS2022 is `MSVC v143 - VS 2022 C++ ARM64 build tools (Latest)`. Now you can add the rust target with `rustup target add aarch64-pc-windows-msvc` and then use the above-mentioned method to compile your app: * npm 
  ```sh
  npm run tauri build -- --target aarch64-pc-windows-msvc
  ```
 * yarn 
  ```sh
  yarn tauri build --target aarch64-pc-windows-msvc
  ```
 * pnpm 
  ```sh
  pnpm tauri build --target aarch64-pc-windows-msvc
  ```
 * deno 
  ```sh
  deno task tauri build --target aarch64-pc-windows-msvc
  ```
 * bun 
  ```sh
  bun tauri build --target aarch64-pc-windows-msvc
  ```
 * cargo 
  ```sh
  cargo tauri build --target aarch64-pc-windows-msvc
  ```
 Note Note that the NSIS installer itself will still be x86 running on the ARM machine via emulation. The app itself will be a native ARM64 binary. ## Supporting Windows 7 By default, the Microsoft Installer (`.msi`) does not work on Windows 7 because it needs to download the WebView2 bootstrapper if not installed (which might fail if TLS 1.2 is not enabled in the operating system). Tauri includes an option to embed the WebView2 bootstrapper (see the [Embedding the WebView2 Bootstrapper](#embedded-bootstrapper) section below). The NSIS based installer (`-setup.exe`) also supports the `downloadBootstrapper` mode on Windows 7. Additionally, to use the Notification API in Windows 7, you need to enable the `windows7-compat` Cargo feature: Cargo.toml 
```toml
[dependencies]
tauri-plugin-notification = { version = "2.0.0", features = [ "windows7-compat" ] }
```
 ## FIPS Compliance If your system requires the MSI bundle to be FIPS compliant you can set the `TAURI_BUNDLER_WIX_FIPS_COMPLIANT` environment variable to `true` before running `tauri build`. In PowerShell you can set it for the current terminal session like this: 
```powershell
$env:TAURI_BUNDLER_WIX_FIPS_COMPLIANT="true"
```
 ## WebView2 Installation Options The installers by default download the WebView2 bootstrapper and executes it if the runtime is not installed. Alternatively, you can embed the bootstrapper, embed the offline installer, or use a fixed WebView2 runtime version. See the following table for a comparison between these methods: | Installation Method | Requires Internet Connection? | Additional Installer Size | Notes | | -------------------------------------------------- | ----------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------- | | [`downloadBootstrapper`](#downloaded-bootstrapper) | Yes | 0MB | `Default` Results in a smaller installer size, but is not recommended for Windows 7 deployment via `.msi` files. | | [`embedBootstrapper`](#embedded-bootstrapper) | Yes | \~1.8MB | Better support on Windows 7 for `.msi` installers. | | [`offlineInstaller`](#offline-installer) | No | \~127MB | Embeds WebView2 installer. Recommended for offline environments. | | [`fixedVersion`](#fixed-version) | No | \~180MB | Embeds a fixed WebView2 version. | | [`skip`](#skipping-installation) | No | 0MB | ⚠️ Not recommended Does not install the WebView2 as part of the Windows Installer. | Note On Windows 10 (April 2018 release or later) and Windows 11, the WebView2 runtime is distributed as part of the operating system. ### Downloaded Bootstrapper This is the default setting for building the Windows Installer. It downloads the bootstrapper and runs it. Requires an internet connection but results in a smaller installer size. This is not recommended if you’re going to be distributing to Windows 7 via `.msi` installers. tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "webviewInstallMode": {
        "type": "downloadBootstrapper"
      }
    }
  }
}
```
 ### Embedded Bootstrapper To embed the WebView2 Bootstrapper, set the [webviewInstallMode](/reference/config/#webviewinstallmode) to `embedBootstrapper`. This increases the installer size by around 1.8MB, but increases compatibility with Windows 7 systems. tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "webviewInstallMode": {
        "type": "embedBootstrapper"
      }
    }
  }
}
```
 ### Offline Installer To embed the WebView2 Bootstrapper, set the [webviewInstallMode](/reference/config/#webviewinstallmode) to `offlineInstaller`. This increases the installer size by around 127MB, but allows your application to be installed even if an internet connection is not available. tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "webviewInstallMode": {
        "type": "offlineInstaller"
      }
    }
  }
}
```
 ### Fixed Version Using the runtime provided by the system is great for security as the webview vulnerability patches are managed by Windows. If you want to control the WebView2 distribution on each of your applications (either to manage the release patches yourself or distribute applications on environments where an internet connection might not be available) Tauri can bundle the runtime files for you. Caution Distributing a fixed WebView2 Runtime version increases the Windows Installer by around 180MB. 1. Download the WebView2 fixed version runtime from [Microsoft’s website](https://developer.microsoft.com/en-us/microsoft-edge/webview2/#download-section). In this example, the downloaded filename is `Microsoft.WebView2.FixedVersionRuntime.128.0.2739.42.x64.cab` 2. Extract the file to the core folder: 
```powershell
Expand .\Microsoft.WebView2.FixedVersionRuntime.128.0.2739.42.x64.cab -F:* ./src-tauri
```
 3. Configure the WebView2 runtime path in `tauri.conf.json`: tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "webviewInstallMode": {
        "type": "fixedRuntime",
        "path": "./Microsoft.WebView2.FixedVersionRuntime.98.0.1108.50.x64/"
      }
    }
  }
}
```
 4. Run `tauri build` to produce the Windows Installer with the fixed WebView2 runtime. ### Skipping Installation You can remove the WebView2 Runtime download check from the installer by setting [webviewInstallMode](/reference/config/#webviewinstallmode) to `skip`. Your application WILL NOT work if the user does not have the runtime installed. Your application WILL NOT work if the user does not have the runtime installed and won’t attempt to install it. tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "webviewInstallMode": {
        "type": "skip"
      }
    }
  }
}
```
 ## Minimum Webview2 version If your app requires features only available in newer Webview2 versions (such as custom URI schemes), you can instruct the Windows installer to verify the current Webview2 version and run the Webview2 bootstrapper if it does not match the target version. tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "minimumWebview2Version": "110.0.1531.0"
    }
  }
}
```
 ## Customizing the WiX Installer See the [WiX configuration](/reference/config/#wixconfig) for the complete list of customization options. ### Installer Template The `.msi` Windows Installer package is built using the [WiX Toolset v3](https://wixtoolset.org/documentation/manual/v3/). Currently, apart from pre-defined [configurations](/reference/config/#wixconfig), you can change it by using a custom WiX source code (an XML file with a `.wxs` file extension) or through WiX fragments. #### Replacing the Installer Code with a Custom WiX File The Windows Installer XML defined by Tauri is configured to work for the common use case of simple webview-based applications (you can find it [here](https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-bundler/src/bundle/windows/msi/main.wxs)). It uses [handlebars](https://docs.rs/handlebars/latest/handlebars/) so the Tauri CLI can brand your installer according to your `tauri.conf.json` definition. If you need a completely different installer, a custom template file can be configured on [`tauri.bundle.windows.wix.template`](/reference/config/#template-2). #### Extending the Installer with WiX Fragments A [WiX fragment](https://wixtoolset.org/documentation/manual/v3/xsd/wix/fragment.html) is a container where you can configure almost everything offered by WiX. In this example, we will define a fragment that writes two registry entries: 
```xml
<?xml version="1.0" encoding="utf-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Fragment>
    <!-- these registry entries should be installed
     to the target user's machine -->
    <DirectoryRef Id="TARGETDIR">
      <!-- groups together the registry entries to be installed -->
      <!-- Note the unique `Id` we provide here -->
      <Component Id="MyFragmentRegistryEntries" Guid="*">
        <!-- the registry key will be under
       HKEY_CURRENT_USER\Software\MyCompany\MyApplicationName -->
        <!-- Tauri uses the second portion of the
       bundle identifier as the `MyCompany` name
       (e.g. `tauri-apps` in `com.tauri-apps.test`)  -->
        <RegistryKey
          Root="HKCU"
          Key="Software\MyCompany\MyApplicationName"
          Action="createAndRemoveOnUninstall"
        >
          <!-- values to persist on the registry -->
          <RegistryValue
            Type="integer"
            Name="SomeIntegerValue"
            Value="1"
            KeyPath="yes"
          />
          <RegistryValue Type="string" Value="Default Value" />
        </RegistryKey>
      </Component>
    </DirectoryRef>
  </Fragment>
</Wix>
```
 Save the fragment file with the `.wxs` extension in the `src-tauri/windows/fragments` folder and reference it on `tauri.conf.json`: tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "wix": {
        "fragmentPaths": ["./windows/fragments/registry.wxs"],
        "componentRefs": ["MyFragmentRegistryEntries"]
      }
    }
  }
}
```
 Note that `ComponentGroup`, `Component`, `FeatureGroup`, `Feature` and `Merge` element ids must be referenced on the `wix` object of `tauri.conf.json` on the `componentGroupRefs`, `componentRefs`, `featureGroupRefs`, `featureRefs` and `mergeRefs` respectively to be included in the installer. ### Internationalization The WiX Installer is built using the `en-US` language by default. Internationalization (i18n) can be configured using the [`tauri.bundle.windows.wix.language`](/reference/config/#language) property, defining the languages Tauri should build an installer against. You can find the language names to use in the Language-Culture column on [Microsoft’s website](https://docs.microsoft.com/en-us/windows/win32/msi/localizing-the-error-and-actiontext-tables). #### Compiling a WiX Installer for a Single Language To create a single installer targeting a specific language, set the `language` value to a string: tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "wix": {
        "language": "fr-FR"
      }
    }
  }
}
```
 #### Compiling a WiX Installer for Each Language in a List To compile an installer targeting a list of languages, use an array. A specific installer for each language will be created, with the language key as a suffix: tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "wix": {
        "language": ["en-US", "pt-BR", "fr-FR"]
      }
    }
  }
}
```
 #### Configuring the WiX Installer Strings for Each Language A configuration object can be defined for each language to configure localization strings: tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "wix": {
        "language": {
          "en-US": null,
          "pt-BR": {
            "localePath": "./wix/locales/pt-BR.wxl"
          }
        }
      }
    }
  }
}
```
 The `localePath` property defines the path to a language file, a XML configuring the language culture: 
```xml
<WixLocalization
  Culture="en-US"
  xmlns="http://schemas.microsoft.com/wix/2006/localization"
>
  <String Id="LaunchApp"> Launch MyApplicationName </String>
  <String Id="DowngradeErrorMessage">
    A newer version of MyApplicationName is already installed.
  </String>
  <String Id="PathEnvVarFeature">
    Add the install location of the MyApplicationName executable to
    the PATH system environment variable. This allows the
    MyApplicationName executable to be called from any location.
  </String>
  <String Id="InstallAppFeature">
    Installs MyApplicationName.
  </String>
</WixLocalization>
```
 Note The `WixLocalization` element’s `Culture` field must match the configured language. Currently, Tauri references the following locale strings: `LaunchApp`, `DowngradeErrorMessage`, `PathEnvVarFeature` and `InstallAppFeature`. You can define your own strings and reference them on your custom template or fragments with `"!(loc.TheStringId)"`. See the [WiX localization documentation](https://wixtoolset.org/documentation/manual/v3/howtos/ui_and_localization/make_installer_localizable.html) for more information. ## Customizing the NSIS Installer See the [NSIS configuration](/reference/config/#nsisconfig) for the complete list of customization options. ### Installer Template The NSIS Installer’s `.nsi` script defined by Tauri is configured to work for the common use case of simple webview-based applications (you can find it [here](https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-bundler/src/bundle/windows/nsis/installer.nsi)). It uses [handlebars](https://docs.rs/handlebars/latest/handlebars/) so the Tauri CLI can brand your installer according to your `tauri.conf.json` definition. If you need a completely different installer, a custom template file can be configured on [`tauri.bundle.windows.nsis.template`](/reference/config/#template-1). ### Extending the Installer If you only need to extend some installation steps you might be able to use installer hooks instead of replacing the entire installer template. Supported hooks are: * `NSIS_HOOK_PREINSTALL`: Runs before copying files, setting registry key values and creating shortcuts. * `NSIS_HOOK_POSTINSTALL`: Runs after the installer has finished copying all files, setting the registry keys and created shortcuts. * `NSIS_HOOK_PREUNINSTALL`: Runs before removing any files, registry keys and shortcuts. * `NSIS_HOOK_POSTUNINSTALL`: Runs after files, registry keys and shortcuts have been removed. For example, create a `hooks.nsh` file in the `src-tauri/windows` folder and define the hooks you need: 
```nsh
!macro NSIS_HOOK_PREINSTALL
  MessageBox MB_OK "PreInstall"
!macroend


!macro NSIS_HOOK_POSTINSTALL
  MessageBox MB_OK "PostInstall"
!macroend


!macro NSIS_HOOK_PREUNINSTALL
  MessageBox MB_OK "PreUnInstall"
!macroend


!macro NSIS_HOOK_POSTUNINSTALL
  MessageBox MB_OK "PostUninstall"
!macroend
```
 Then you must configure Tauri to use that hook file: tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "nsis": {
        "installerHooks": "./windows/hooks.nsh"
      }
    }
  }
}
```
 #### Including Files Next to the Hook Tauri includes your hook file from its generated NSIS script using `!include`. At the top level of the hook file, `${__FILEDIR__}` refers to the hook file’s directory, so you can include a file beside it directly. Macro bodies, however, are expanded where Tauri inserts them into the generated script. Inside a hook macro, `${__FILEDIR__}` therefore refers to the generated script’s directory instead. If a macro needs a file beside the hook, capture the hook directory in a top-level `!define` first: 
```nsh
!include "${__FILEDIR__}\adjacent.nsh"
!define HOOK_FILE_DIR "${__FILEDIR__}"


!macro NSIS_HOOK_PREINSTALL
  File "${HOOK_FILE_DIR}\example.txt"
!macroend
```
 #### Installing Dependencies with Hooks You can use installer hooks to automatically install system dependencies that your application requires. This is particularly useful for runtime dependencies like Visual C++ Redistributables, DirectX, OpenSSL or other system libraries that may not be present on all Windows systems. **MSI Installer Example (Visual C++ Redistributable):** 
```nsh
!macro NSIS_HOOK_POSTINSTALL
  ; Check if Visual C++ 2019 Redistributable is installed (via Windows Registry)
  ReadRegDWord $0 HKLM "SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" "Installed"


  ${If} $0 == 1
    DetailPrint "Visual C++ Redistributable already installed"
    Goto vcredist_done
  ${EndIf}


  ; Install from bundled MSI if not installed
  ${If} ${FileExists} "$INSTDIR\resources\vc_redist.x64.msi"
    DetailPrint "Installing Visual C++ Redistributable..."
    ; Copy to TEMP folder and then execute installer
    CopyFiles "$INSTDIR\resources\vc_redist.x64.msi" "$TEMP\vc_redist.x64.msi"
    ExecWait 'msiexec /i "$TEMP\vc_redist.x64.msi" /passive /norestart' $0


    ; Check whether installation process exited successfully (code 0) or not
    ${If} $0 == 0
      DetailPrint "Visual C++ Redistributable installed successfully"
    ${Else}
      MessageBox MB_ICONEXCLAMATION "Visual C++ installation failed. Some features may not work."
    ${EndIf}


    ; Clean up setup files from TEMP and your installed app
    Delete "$TEMP\vc_redist.x64.msi"
    Delete "$INSTDIR\resources\vc_redist.x64.msi"
  ${EndIf}


  vcredist_done:
!macroend
```
 **Key considerations:** * A good practice is to always check if the dependency is already installed using registry keys or file existence or via Windows [where](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/where) command. * Use `/passive`, `/quiet`, or `/silent` flags to avoid interrupting the installation flow. Check out [msiexec](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/msiexec) options for `.msi` files, or the setup manual for app-specific flags * Include `/norestart` to prevent automatic system reboots during installation for setups that restarts user devices * Clean up temporary files and bundled installers to avoid bloating the application * Consider that dependencies might be shared with other applications when uninstalling * Provide meaningful error messages if installation fails Ensure to bundle the dependency installers in your `src-tauri/resources` folder and add to `tauri.conf.json` so they get bundled, and can be accessed during installation from `$INSTDIR\resources\`: tauri.conf.json 
```json
{
  "bundle": {
    "resources": [
      "resources/my-dependency.exe",
      "resources/another-one.msi"
    ]
  }
}
```
 ### Install Modes By default the installer will install your application for the current user only. The advantage of this option is that the installer does not require Administrator privileges to run, but the app is installed in the `%LOCALAPPDATA%` folder instead of `C:/Program Files`. If you prefer your app installation to be available system-wide (which requires Administrator privileges) you can set [installMode](/reference/config/#installmode) to `perMachine`: tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "nsis": {
        "installMode": "perMachine"
      }
    }
  }
}
```
 Alternatively you can let the user choose whether the app should be installed for the current user only or system-wide by setting the [installMode](/reference/config/#installmode) to `both`. Note that the installer will require Administrator privileges to execute. See [NSISInstallerMode](/reference/config/#nsisinstallermode) for more information. ### Internationalization The NSIS Installer is a multi-language installer, which means you always have a single installer which contains all the selected translations. You can specify which languages to include using the [`tauri.bundle.windows.nsis.languages`](/reference/config/#languages) property. A list of languages supported by NSIS is available in [the NSIS GitHub project](https://github.com/kichik/nsis/tree/9465c08046f00ccb6eda985abbdbf52c275c6c4d/Contrib/Language%20files). There are a few [Tauri-specific translations](https://github.com/tauri-apps/tauri/tree/dev/crates/tauri-bundler/src/bundle/windows/nsis/languages) required, so if you see untranslated texts feel free to open a feature request in [Tauri’s main repo](https://github.com/tauri-apps/tauri/issues/new?assignees=\&labels=type%3A+feature+request\&template=feature_request.yml\&title=%5Bfeat%5D+). You can also provide [custom translation files](/reference/config/#customlanguagefiles). By default the operating system default language is used to determine the installer language. You can also configure the installer to display a language selector before the installer contents are rendered: tauri.conf.json 
```json
{
  "bundle": {
    "windows": {
      "nsis": {
        "displayLanguageSelector": true
      }
    }
  }
}
```

# Learn

> Tutorials intended to provide end-to-end learning experiences to guide you through specific Tauri topics and help you apply knowledge from the guides and reference documentation

The Learning category is intended to provide end-to-end learning experiences on a Tauri related topic. These tutorials will guide you through a specific topic and help you apply knowledge from the guides and reference documentation. For security related topics, you can learn about the permissions system. You will get practical insight into how to use it, extend it, and write your own permissions. [Using Plugin Permissions](/learn/security/using-plugin-permissions/) [Capabilities for Different Windows and Platforms](/learn/security/capabilities-for-windows-and-platforms/) [Writing Plugin Permissions](/learn/security/writing-plugin-permissions/) To learn how to write your own splash screen, use a Node.js sidecar, or set up mobile features, check out: [Splash Screen](/learn/splashscreen/) [Node.js as a Sidecar](/learn/sidecar-nodejs/) [Multi-Window on Mobile](/learn/mobile-multiwindow/) [File Associations on Mobile](/learn/mobile-file-associations/) ## More Resources This section contains learning resources created by the Community that are not hosted on this website. [Have something to share?](https://github.com/tauri-apps/awesome-tauri/pulls)Open a pull request to show us your amazing resource. ### Books ![HTML, CSS, JavaScript, and Rust for Beginners Book Cover](/_astro/HTML_CSS_JavaScript_and_Rust_for_Beginners_A_Guide_to_Application_Development_with_Tauri.DmlndB-D_Z1aSg74.webp) ### HTML, CSS, JavaScript, and Rust for Beginners: A Guide to Application Development with Tauri by James Alexander Rose Paperback on Amazon: [Buy Here](https://www.amazon.com/dp/B0DR6KZVVW) Free PDF version: [Download (PDF 4MB)](/assets/learn/community/HTML_CSS_JavaScript_and_Rust_for_Beginners_A_Guide_to_Application_Development_with_Tauri.pdf) ### Guides & Tutorials [Auto-Updates with Tauri v2](https://docs.crabnebula.dev/guides/auto-updates-tauri)Setup auto-updates with Tauri and CrabNebula Cloud. [Publish to Apple’s App Store](https://thinkgo.io/post/2023/02/publish_tauri_to_apples_app_store/)Details all the steps needed to publish your Mac app to the app store. Includes a sample bash script. #### Video Guides [Create Tauri App with React](https://www.youtube.com/watch?v=zawhqLA7N9Y\&ab_channel=chrisbiscardi)Chris Biscardi shows how easy it is to wire up a Rust crate with a JS module and communicate between them. [Tauri & ReactJS - Creating Modern Desktop Apps](https://youtube.com/playlist?list=PLmWYh0f8jKSjt9VC5sq2T3mFETasG2p2L)Creating a modern desktop application with Tauri.

# File Associations on Mobile

Tauri supports file associations on Android and iOS, allowing your app to be registered as a handler for specific file types. When a user opens a file that matches your declared associations, the operating system launches your app and delivers the file URL. On **Android**, file associations are implemented using [intent filters](https://developer.android.com/training/app-links/deep-linking) that the Tauri build system generates automatically from your configuration. On **iOS**, file associations use [CFBundleDocumentTypes](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundledocumenttypes) and optionally [UTExportedTypeDeclarations](https://developer.apple.com/documentation/bundleresources/information-property-list/utexportedtypedeclarations) for custom file types. ## Configuration File associations are declared in `tauri.conf.json` under `bundle.fileAssociations`. The Tauri CLI uses this configuration to generate the appropriate platform-specific metadata (Android intent filters in `AndroidManifest.xml`, iOS document types in `Info.plist`). Each entry in the array represents a file type your app can handle: src-tauri/tauri.conf.json 
```json
{
  "bundle": {
    "fileAssociations": [
      {
        "ext": ["png"],
        "mimeType": "image/png"
      },
      {
        "ext": ["jpg", "jpeg"],
        "mimeType": "image/jpeg"
      }
    ]
  }
}
```
 ### Configuration Options * `ext` — list of file extensions to associate (without leading dot). * `mimeType` — the MIME type for the file (e.g. `image/png`). Required on Android for intent filter matching. Tauri infers common MIME types from extensions when not specified. * `role` — the app’s role with respect to the file type. Maps to `CFBundleTypeRole` on Apple platforms. Values: `Editor` (default), `Viewer`, `Shell`, `QLGenerator`, `None`. * `rank` — the ranking among apps that handle this file type. Maps to `LSHandlerRank` on Apple platforms. Values: `Default` (default), `Owner`, `Alternate`, `None`. * `name` — display name for the file type. Defaults to the first extension. * `exportedType` — defines a custom file type owned by your app. Required on Apple platforms when associating with non-standard file extensions. * `androidIntentActionFilters` — which Android intent actions to register. Values: `Send`, `SendMultiple`, `View`. All three are used by default. ### Custom File Types For non-standard file extensions, you should define an `exportedType` so Apple platforms can identify the file type. The `identifier` should be a reverse-DNS string unique to your app, and `conformsTo` lists the parent types: src-tauri/tauri.conf.json 
```json
{
  "bundle": {
    "fileAssociations": [
      {
        "ext": ["mydata"],
        "mimeType": "application/octet-stream",
        "exportedType": {
          "identifier": "com.example.myapp.mydata",
          "conformsTo": ["public.data"]
        }
      }
    ]
  }
}
```
 Common `conformsTo` values include `public.data`, `public.image`, `public.json`, and `public.plain-text`. ## Handling Opened Files When a file is opened with your app, Tauri emits a `RunEvent::Opened` event containing the file URLs. This event is available on macOS, iOS, and Android. You need to handle two cases: 1. **App is already running** — the event is delivered at runtime. 2. **App is launched by the file open** — the event fires during startup, so you should store the URLs and make them available to your frontend. ### Rust Store incoming URLs in managed state, expose them with a command the frontend can call on startup, and emit a Tauri event whenever `RunEvent::Opened` fires so the frontend can react while the app is already running: src-tauri/src/lib.rs 
```rust
use std::sync::Mutex;
use tauri::Manager;


struct OpenedUrls(Mutex<Vec<tauri::Url>>);


#[tauri::command]
fn opened_urls(app: tauri::AppHandle) -> Vec<tauri::Url> {
    app.state::<OpenedUrls>().0.lock().unwrap().clone()
}


#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(OpenedUrls(Mutex::new(vec![])))
        .invoke_handler(tauri::generate_handler![opened_urls])
        .build(tauri::generate_context!())
        .expect("error while running tauri application")
        .run(|app, event| {
            #[cfg(any(target_os = "macos", target_os = "ios", target_os = "android"))]
            if let tauri::RunEvent::Opened { urls } = event {
                use tauri::Emitter;
                app.state::<OpenedUrls>()
                    .0
                    .lock()
                    .unwrap()
                    .extend(urls.clone());
                app.emit("opened", urls).unwrap();
            }
        });
}
```
 ### JavaScript The frontend below is wired to that Rust code in two places: * **`invoke('opened_urls')`** calls the `opened_urls` command, so the webview can read URLs that were stored before the UI finished loading (cold start from a file open). * **`listen('opened', …)`** subscribes to the same event name passed to **`app.emit("opened", urls)`** in Rust, so file open events that are triggered while the app is already running are delivered immediately. 
```javascript
import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';


// Cold start: URLs may already be in Rust state before the frontend loads
const initialUrls = await invoke('opened_urls');
if (initialUrls.length > 0) {
  handleFiles(initialUrls);
}


// Warm: Rust emits the "opened" event when RunEvent::Opened fires
await listen('opened', (event) => {
  handleFiles(event.payload);
});
```

# Multi-Window on Mobile

Tauri supports multiple windows on Android and iOS, allowing your app to display content side-by-side on tablets or in separate scenes on iPad. On **Android**, multi-window is implemented using [Activity Embedding](https://developer.android.com/guide/topics/large-screens/activity-embedding), which lets the system display two activities side by side on large screens. On **iOS**, multi-window uses the [UIScene](https://developer.apple.com/documentation/uikit/uiscene) API, which allows iPad users to open multiple instances of your app in separate windows. On **phones**, the system usually does not lay out two windows side by side. On **Android**, creating another window still launches a separate activity, but on handset-sized displays it is typically **pushed onto the activity back stack**—so **Back** returns to the previous activity instead of closing a split. On **iOS** (especially iPhone), opening or creating another window often **replaces the current UI** with the new scene’s content rather than keeping both visible at once; true concurrent windows remain an **iPad** (and Stage Manager) experience. Note Multi-window requires Android 12L (API 32)+ and iOS 13+. You can use the \[`app.supportsMultipleWindows`] API to check availability at runtime. ## Shared Setup Both platforms require a capability permission to create new windows from the frontend. ### Capabilities Add the `core:webview:allow-create-webview-window` permission to your capability file so your frontend can create new windows. If you are creating multiple windows, use a wildcard or list every window label in the `windows` array: src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  +"permissions": ["core:default", "core:webview:allow-create-webview-window"]
}
```
 ## Android Android multi-window uses [Activity Embedding](https://developer.android.com/guide/topics/large-screens/activity-embedding) to split activities side by side on large screens (tablets, foldables). You need to create an Android `Activity` for each window type, configure split rules, and register an initializer. 1. ### Add Dependencies Add the required AndroidX libraries to your `build.gradle.kts`: src-tauri/gen/android/app/build.gradle.kts 
   ```diff
   dependencies {
       // ... existing dependencies
       +implementation("androidx.window:window:1.5.0")
       +implementation("androidx.startup:startup-runtime:1.2.0")
   }
   ```
 2. ### Create a New Activity Create a Kotlin class for each additional window type. Each activity must extend `TauriActivity`: src-tauri/gen/android/app/src/main/java/com/example/app/DetailActivity.kt 
   ```kotlin
   package com.example.app


   import android.os.Bundle
   import android.os.PersistableBundle


   class DetailActivity: TauriActivity() {
     override fun onCreate(savedInstanceState: Bundle?) {
       super.onCreate(savedInstanceState)
     }
   }
   ```
 3. ### Update AndroidManifest.xml Register the new activity and enable activity embedding by adding the `tools` namespace and the embedding property: src-tauri/gen/android/app/src/main/AndroidManifest.xml 
   ```diff
   <?xml version="1.0" encoding="utf-8"?>
   <manifest xmlns:android="http://schemas.android.com/apk/res/android"
     +xmlns:tools="http://schemas.android.com/tools">


     <application ...>


       <property
         +android:name="android.window.PROPERTY_ACTIVITY_EMBEDDING_SPLITS_ENABLED"
         +android:value="true" />


       <!-- Existing MainActivity -->
       <activity
         android:name=".MainActivity"
         android:exported="true"
         ...>
         ...
       </activity>


       <!-- New activity for the detail window -->
       <activity android:name=".DetailActivity" android:exported="true" />


       +<!-- Register the split initializer -->
       <provider android:name="androidx.startup.InitializationProvider"
         +android:authorities="${applicationId}.androidx-startup"
         +android:exported="false"
         +tools:node="merge">
         <meta-data android:name="${applicationId}.SplitInitializer"
           +android:value="androidx.startup" />
       </provider>


     </application>
   </manifest>
   ```
 4. ### Create the Split Initializer The initializer loads the split pair rules at app startup: src-tauri/gen/android/app/src/main/java/com/example/app/SplitInitializer.kt 
   ```kotlin
   package com.example.app


   import android.content.Context
   import androidx.startup.Initializer
   import androidx.window.core.ExperimentalWindowApi
   import androidx.window.embedding.RuleController


   @OptIn(ExperimentalWindowApi::class)
   class SplitInitializer : Initializer<RuleController> {
     override fun create(context: Context): RuleController {
       return RuleController.getInstance(context).apply {
         setRules(RuleController.parseRules(context, R.xml.main_split_config))
       }
     }


     override fun dependencies(): List<Class<out Initializer<*>>> {
       return emptyList()
     }
   }
   ```
 5. ### Define Split Rules Create an XML resource that tells the system how to pair activities and split the screen: src-tauri/gen/android/app/src/main/res/xml/main_split_config.xml 
   ```xml
   <resources
     xmlns:window="http://schemas.android.com/apk/res-auto">


     <SplitPairRule
       window:splitRatio="0.33"
       window:splitLayoutDirection="locale"
       window:splitMinWidthDp="840"
       window:splitMaxAspectRatioInPortrait="alwaysAllow"
       window:finishPrimaryWithSecondary="never"
       window:finishSecondaryWithPrimary="never"
       window:clearTop="false">
       <SplitPairFilter
         window:primaryActivityName=".MainActivity"
         window:secondaryActivityName=".DetailActivity"/>
     </SplitPairRule>


   </resources>
   ```
 Key attributes: * `splitRatio` — how the screen is divided (0.33 gives the primary activity one-third) * `splitMinWidthDp` — minimum screen width to activate the split (840dp targets tablets) * `splitMaxAspectRatioInPortrait` — set to `alwaysAllow` to enable split in portrait mode * `primaryActivityName` / `secondaryActivityName` — which activity pair triggers the split ## iOS On iOS, multi-window uses the UIScene API. iPad users can open new windows by long-pressing the app icon and selecting “New window”, or your app can create them programmatically. 1. ### Enable Scene Support Create an `Info.ios.plist` file in your `src-tauri` directory to declare scene support: src-tauri/Info.ios.plist 
   ```diff
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
     "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
     <key>UIApplicationSceneManifest</key>
     <dict>
       <key>UIApplicationSupportsMultipleScenes</key>
       <true/>
       <key>UISceneConfigurations</key>
       <dict/>
     </dict>
   </dict>
   </plist>
   ```
 2. ### Handle Scene Requests When a user requests a new window on iPad (for example by long-pressing the app icon), Tauri emits a `RunEvent::SceneRequested` event. Handle it to create a new window: src-tauri/src/lib.rs 
   ```rust
   #[cfg_attr(mobile, tauri::mobile_entry_point)]
   pub fn run() {
       #[cfg(target_os = "ios")]
       let mut counter = 0;


       tauri::Builder::default()
           .setup(|app| {
               tauri::WebviewWindowBuilder::new(
                   app, "main", tauri::WebviewUrl::default()
               ).build()?;
               Ok(())
           })
           .build(tauri::generate_context!())
           .expect("error while running tauri application")
           .run(move |app, event| {
               #[cfg(target_os = "ios")]
               if let tauri::RunEvent::SceneRequested { .. } = event {
                   counter += 1;
                   tauri::WebviewWindowBuilder::new(
                       app,
                       format!("main-{counter}"),
                       tauri::WebviewUrl::default(),
                   )
                   .build()
                   .unwrap();
               }
               #[cfg(not(target_os = "ios"))]
               let _ = (app, event);
           });
   }
   ```
 Note Since scene-requested windows use dynamic labels like `main-1`, `main-2`, etc., make sure your capabilities file includes a wildcard pattern to cover them — e.g. `"windows": ["main", "main-*"]`. ## Creating Windows You can create additional windows from both Rust and the frontend JavaScript API. The `WebviewWindowBuilder` (Rust) and `WebviewWindow` (JavaScript) accept platform-specific options: Android options: * `activityName` — the name of the Android Activity class to create for this window. * `createdByActivityName` — the name of the Activity that is creating this window. This determines which activity stack the new activity belongs to, which is important for the split rules to work correctly. When not set, it is automatically inherited from the manager (e.g. when building from a `Window` or `Webview` handle). iOS options: * `requestedBySceneIdentifier` — sets the identifier of the UIScene that is requesting the creation of this new scene, establishing a relationship between the two scenes. By default the system uses the foreground scene. When not set, it is automatically inherited from the manager. - JavaScript 
  ```javascript
  import { WebviewWindow } from '@tauri-apps/api/webviewWindow';


  function openDetail(id) {
    const webview = new WebviewWindow(`detail-${id}`, {
      url: `detail/${id}`,
      activityName: 'DetailActivity',
    });
    webview.once('tauri://created', () => {
      console.log('window created');
    });
    webview.once('tauri://error', (e) => {
      console.error(e);
    });
  }
  ```
 - Rust 
  ```rust
  use tauri::Manager;


  let main_window = app.get_webview_window("main").unwrap();
  // use the main_window instance so the relationships are determined automatically
  let builder = tauri::WebviewWindowBuilder::new(main_window, "detail", tauri::WebviewUrl::App("detail/1".into()));


  #[cfg(target_os = "android")]
  let builder = builder.activity_name("DetailActivity");


  let window = builder.build()?;
  ```
 ## Window Instance APIs Once a window has been created, you can retrieve its platform-specific identifier: * JavaScript 
  ```javascript
  const activityName = await window.activityName();
  const sceneId = await window.sceneIdentifier();
  ```
 * Rust 
  ```rust
  #[cfg(target_os = "android")]
  let activity = window.activity_name()?;


  #[cfg(target_os = "ios")]
  let scene_id = window.scene_identifier()?;
  ```
 These getters are useful for referencing a window’s identity when creating related windows. For example, you can read a window’s `activityName` to pass as `createdByActivityName` on a new window, or read `sceneIdentifier` to pass as `requestedBySceneIdentifier`.

# Capabilities for Different Windows and Platforms

This guide will help you customize the capabilities of your Tauri app. ## Content of this guide * Create multiple windows in a Tauri app * Use different capabilities for different windows * Use platform-specific capabilities ## Prerequisites This exercise is meant to be read after completing [`Using Plugin Permissions`](/learn/security/using-plugin-permissions/). ## Guide 1. ### Create Multiple Windows in a Tauri Application Here we create an app with two windows labelled `first` and `second`. There are multiple ways to create windows in your Tauri application. #### Create Windows with the Tauri Configuration File In the Tauri configuration file, usually named `tauri.conf.json`: Show solution 
   ```javascript
     "productName": "multiwindow",
     ...
     "app": {
       "windows": [
         {
           "label": "first",
           "title": "First",
           "width": 800,
           "height": 600
         },
         {
           "label": "second",
           "title": "Second",
           "width": 800,
           "height": 600
         }
       ],
     },
     ...
   }
   ```
 #### Create Windows Programmatically In the Rust code to create a Tauri app: Show solution 
   ```rust
   tauri::Builder::default()
       .invoke_handler(tauri::generate_handler![greet])
       .setup(|app| {
           let webview_url = tauri::WebviewUrl::App("index.html".into());
           // First window
           tauri::WebviewWindowBuilder::new(app, "first", webview_url.clone())
               .title("First")
               .build()?;
           // Second window
           tauri::WebviewWindowBuilder::new(app, "second", webview_url)
               .title("Second")
               .build()?;
           Ok(())
       })
       .run(context)
       .expect("error while running tauri application");
   ```
 2. ### Apply Different Capabilities to Different Windows The windows of a Tauri app can use different features or plugins of the Tauri backend. For better security it is recommended to only give the necessary capabilities to each window. We simulate a scenario where the `first` windows uses filesystem and dialog functionalities and `second` only needs dialog functionalities. #### Separate capability files per category It is recommended to separate the capability files per category of actions they enable. Show solution JSON files in the `src-tauri/capabilities` will be taken into account for the capability system. Here we separate capabilities related to the filesystem and dialog window into `filesystem.json` and `dialog.json`. *filetree of the Tauri project:* 
   ```plaintext
   /src
   /src-tauri
     /capabilities
       filesystem.json
       dialog.json
     tauri.conf.json
   package.json
   README.md
   ```
 #### Give filesystem capabilities to the `first` window We give the `first` window the capability to have read access to the content of the `$HOME` directory. Show solution Use the `windows` field in a capability file with one or multiple window labels. filesystem.json 
   ```json
   {
     "identifier": "fs-read-home",
     "description": "Allow access file access to home directory",
     "local": true,
     "windows": ["first"],
     "permissions": [
       "fs:allow-home-read",
     ]
   }
   ```
 #### Give dialog capabilities to the `first` and `second` window We give to `first` and `second` windows the capability to create a “Yes/No” dialog Show solution Use the `windows` field in a capability file with one or multiple window labels. dialog.json 
   ```json
   {
     "identifier": "dialog",
     "description": "Allow to open a dialog",
     "local": true,
     "windows": ["first", "second"],
     "permissions": ["dialog:allow-ask"]
   }
   ```
 3. ### Make Capabilities Platform Dependent We now want to customize the capabilities to be active only on certain platforms. We make our filesystem capabilities only active on `linux` and `windows`. Show solution Use the `platforms` field in a capability file to make it platform-specific. filesystem.json 
   ```json
   {
     "identifier": "fs-read-home",
     "description": "Allow access file access to home directory",
     "local": true,
     "windows": ["first"],
     "permissions": [
       "fs:allow-home-read",
     ],
     "platforms": ["linux", "windows"]
   }
   ```
 The currently available platforms are `linux`, `windows`, `macos`, `android`, and `ios`. ## Conclusion and Resources We have learned how to create multiple windows in a Tauri app and give them specific capabilities. Furthermore these capabilities can also be targeted to certain platforms. An example application that used window capabilities can be found in the [`api` example](https://github.com/tauri-apps/tauri/tree/dev/examples/api) of the [Tauri Github repository](https://github.com/tauri-apps/tauri). The fields that can be used in a capability file are listed in the [Capability](/reference/acl/capability/) reference.

# Using Plugin Permissions

The goal of this exercise is to get a better understanding on how plugin permissions can be enabled or disabled, where they are described and how to use default permissions of plugins. At the end you will have the ability to find and use permissions of arbitrary plugins and understand how to custom tailor existing permissions. You will have an example Tauri application where a plugin and plugin specific permissions are used. 1. ### Create Tauri Application Create your Tauri application. In our example we will facilitate [`create-tauri-app`](https://github.com/tauri-apps/create-tauri-app): * Bash 
     ```sh
     sh <(curl https://create.tauri.app/sh)
     ```
 * PowerShell 
     ```sh
     irm https://create.tauri.app/ps | iex
     ```
 * Fish 
     ```sh
     sh (curl -sSL https://create.tauri.app/sh | psub)
     ```
 * npm 
     ```sh
     npm create tauri-app@latest
     ```
 * Yarn 
     ```sh
     yarn create tauri-app
     ```
 * pnpm 
     ```sh
     pnpm create tauri-app
     ```
 * deno 
     ```sh
     deno run -A npm:create-tauri-app
     ```
 * bun 
     ```sh
     bun create tauri-app
     ```
 * Cargo 
     ```sh
     cargo install create-tauri-app --locked
     cargo create-tauri-app
     ```
 We will proceed in this step-by-step explanation with `pnpm` but you can choose another package manager and replace it in the commands accordingly. Show solution 
   ```plaintext
   pnpm create tauri-app
   ```
 
   ```plaintext
   ✔ Project name · plugin-permission-demo
   ✔ Choose which language to use for your frontend · TypeScript / JavaScript - (pnpm, yarn, npm, bun)
   ✔ Choose your package manager · pnpm
   ✔ Choose your UI template · Vanilla
   ✔ Choose your UI flavor · TypeScript


   Template created! To get started run:
   cd plugin-permission-demo
   pnpm install
   pnpm tauri dev
   ```
 2. ### Add the `file-system` Plugin to Your Application To search for existing plugins you can use multiple resources. The most straight forward way would be to check out if your plugin is already in the [Plugins](/plugin/) section of the documentation and therefore part of Tauri’s maintained plugin set. The Filesystem plugin is part of the Tauri plugin workspace and you can add it to your project by following the [instructions](/plugin/file-system/#setup). If the plugin is part of the community effort you can most likely find it on [crates.io](https://crates.io/search?q=tauri-plugin-) when searching for `tauri-plugin-<your plugin name>`. Show solution If it is an existing plugin from our workspace you can use the automated way: 
   ```plaintext
   pnpm tauri add fs
   ```
 If you have found it on [crates.io](https://crates.io/crates/tauri-plugin-fs) you need to manually add it as a dependency and modify the Tauri builder to initialize the plugin: 
   ```sh
   cargo add tauri-plugin-fs
   ```
 Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
   ```diff
   #[cfg_attr(mobile, tauri::mobile_entry_point)]
   fn run() {
     tauri::Builder::default()
       +.plugin(tauri_plugin_fs::init())
       .run(tauri::generate_context!())
       .expect("error while running tauri application");
   }
   ```
 3. ### Understand the Default Permissions of the `fs` Plugin Each plugin has a `default` permission set, which contains all permissions and scopes to use the plugin out of the box with a reasonable minimal feature set. In the case of official maintained plugins you can find a rendered description in the documentation (eg. [fs default](/plugin/file-system/#default-permission)). In case you are figuring this out for a community plugin you need to check out the source code of the plugin. This should be defined in `your-plugin/permissions/default.toml`. Show solution 
   ```plaintext
   "$schema" = "schemas/schema.json"


   [default]
   description = """
   # Tauri `fs` default permissions


   This configuration file defines the default permissions granted
   to the filesystem.


   ### Granted Permissions


   This default permission set enables all read-related commands and
   allows access to the `$APP` folder and sub directories created in it.
   The location of the `$APP` folder depends on the operating system,
   where the application is run.


   In general the `$APP` folder needs to be manually created
   by the application at runtime, before accessing files or folders
   in it is possible.


   ### Denied Permissions


   This default permission set prevents access to critical components
   of the Tauri application by default.
   On Windows the webview data folder access is denied.


   """
   permissions = ["read-all", "scope-app-recursive", "deny-default"]
   ```
 4. ### Find the Right Permissions This step is all about finding the permissions you need to for your commands to be exposed to the frontend with the minimal access to your system. The `fs` plugin has autogenerated permissions which will disable or enable individual commands and allow or disable global scopes. These can be found in the [documentation](/plugin/file-system/#permission-table) or in the source code of the plugin (`fs/permissions/autogenerated`). Let us assume we want to enable writing to a text file `test.txt` located in the users `$HOME` folder. For this we would search in the autogenerated permissions for a permission to enable writing to text files like `allow-write-text-file` and then for a scope which would allow us to access the `$HOME/test.txt` file. We need to add these to our `capabilities` section in our `src-tauri/tauri.conf.json` or in a file in the `src-tauri/capabilities/` folder. By default there is already a capability in `src-tauri/capabilities/default.json` we can modify. Show solution src-tauri/capabilities/default.json 
   ```diff
   {
     "$schema": "../gen/schemas/desktop-schema.json",
     "identifier": "default",
     "description": "Capability for the main window",
     "windows": [
       "main"
     ],
     "permissions": [
       "path:default",
       "event:default",
       "window:default",
       "app:default",
       "image:default",
       "resources:default",
       "menu:default",
       "tray:default",
       "shell:allow-open",
       -"fs:default",
       +"fs:allow-write-text-file",
     ]
   }
   ```
 Since there are only autogenerated scopes in the `fs` plugin to access the full `$HOME` folder, we need to configure our own scope. This scope should be only enabled for the `write-text-file` command and should only expose our `test.txt` file. Show solution src-tauri/capabilities/default.json 
   ```diff
      {
     "$schema": "../gen/schemas/desktop-schema.json",
     "identifier": "default",
     "description": "Capability for the main window",
     "windows": [
       "main"
     ],
     "permissions": [
       "path:default",
       "event:default",
       "window:default",
       "app:default",
       "image:default",
       "resources:default",
       "menu:default",
       "tray:default",
       "shell:allow-open",
       -"fs:allow-write-text-file",
   +    {
         +"identifier": "fs:allow-write-text-file",
         +"allow": [{ "path": "$HOME/test.txt" }]
   +    },
     ]
   }
   ```
 5. ### Test Permissions in Practice After we have added the necessary permission we want to confirm that our application can access the file and write it’s content. Show solution We can use this snippet in our application to write to the file: src/main.ts 
   ```ts
   import { writeTextFile, BaseDirectory } from '@tauri-apps/plugin-fs';


   let greetInputEl: HTMLInputElement | null;


   async function write(message: string) {
       await writeTextFile('test.txt', message, { baseDir: BaseDirectory.Home });
   }


   window.addEventListener("DOMContentLoaded", () => {
     greetInputEl = document.querySelector("#greet-input");
     document.querySelector("#greet-form")?.addEventListener("submit", (e) => {
       e.preventDefault();
       if (!greetInputEl )
         return;


       write(greetInputEl.value == "" ? "No input provided": greetInputEl.value);


     });
   });
   ```
 Replacing the `src/main.ts` with this snippet means we do not need to modify the default `index.html`, when using the plain Vanilla+Typescript app. Entering any input into the input field of the running app will be written to the file on submit. Let’s test now in practice: 
   ```plaintext
   pnpm run tauri dev
   ```
 After writing into the input and clicking “Submit”, we can check via our terminal emulator or by manually opening the file in your home folder. 
   ```plaintext
   cat $HOME/test.txt
   ```
 You should be presented with your input and finished learning about using permissions from plugins in Tauri applications. 🥳 If you encountered this error: 
   ```sh
   [Error] Unhandled Promise Rejection: fs.write_text_file not allowed. Permissions associated with this command: fs:allow-app-write, fs:allow-app-write-recursive, fs:allow-appcache-write, fs:allow-appcache-write-recursive, fs:allow-appconf...
   (anonymous function) (main.ts:5)
   ```
 Then you very likely did not properly follow the [previous instructions](#find-the-right-permissions).

# Writing Plugin Permissions

The goal of this exercise is to get a better understanding on how plugin permissions can be created when writing your own plugin. At the end you will have the ability to create simple permissions for your plugins. You will have an example Tauri plugin where permissions are partially autogenerated and hand crafted. 1. ### Create a Tauri Plugin In our example we will facilitate the Tauri [`cli`](/reference/cli/) to bootstrap a Tauri plugin source code structure. Make sure you have installed all [Prerequisites](/start/prerequisites/) and verify you have the Tauri CLI in the correct version by running `cargo tauri info`. The output should indicate the `tauri-cli` version is `2.x`. We will proceed in this step-by-step explanation with `pnpm` but you can choose another package manager and replace it in the commands accordingly. Once you have a recent version installed you can go ahead and create the plugin using the Tauri CLI. Show solution 
   ```sh
   mkdir -p tauri-learning
   cd tauri-learning
   cargo tauri plugin new test
   cd tauri-plugin-test
   pnpm install
   pnpm build
   cargo build
   ```
 2. ### Create a New Command To showcase something practical and simple let us assume our command writes user input to a file in our temporary folder while adding some custom header to the file. Let’s name our command `write_custom_file`, implement it in `src/commands.rs` and add it to our plugin builder to be exposed to the frontend. Tauri’s core utils will autogenerate `allow` and `deny` permissions for this command, so we do not need to care about this. Show solution The command implementation: src/commands.rs 
   ```diff
   use tauri::{AppHandle, command, Runtime};


   use crate::models::*;
   use crate::Result;
   use crate::TestExt;


   #[command]
   pub(crate) async fn ping<R: Runtime>(
       app: AppHandle<R>,
       payload: PingRequest,
   ) -> Result<PingResponse> {
       app.test1().ping(payload)
   }


   +#[command]
   +pub(crate) async fn write_custom_file<R: Runtime>(
       +user_input: String,
       +app: AppHandle<R>,
   +) -> Result<String> {
   +    std::fs::write(app.path().temp_dir().unwrap(), user_input)?;
   +    Ok("success".to_string())
   +}
   ```
 Auto-Generate inbuilt permissions for your new command: src/build.rs 
   ```rust
   const COMMANDS: &[&str] = &["ping", "write_custom_file"];
   ```
 These inbuilt permissions will be automatically generated by the Tauri build system and will be visible in the `permissions/autogenerated/commands` folder. By default an `enable-<command>` and `deny-<command>` permission will be created. 3. ### Expose the New Command The previous step was to write the actual command implementation. Next we want to expose it to the frontend so it can be consumed. Show solution Configure the Tauri builder to generate the invoke handler to pass frontend IPC requests to the newly implemented command: src/lib.rs 
   ```rust
   pub fn init<R: Runtime>() -> TauriPlugin<R> {
   Builder::new("test")
       .invoke_handler(tauri::generate_handler![
           commands::ping,
           commands::write_custom_file,
       ])
       .setup(|app, api| {
           #[cfg(mobile)]
           let test = mobile::init(app, api)?;
           #[cfg(desktop)]
           let test = desktop::init(app, api)?;
           app.manage(test);


           // manage state so it is accessible by the commands
           app.manage(MyState::default());
           Ok(())
       })
       .build()
   }
   ```
 Expose the new command in the frontend module. This step is essential for the example application to successfully import the frontend module. This is for convenience and has no security impact, as the command handler is already generated and the command can be manually invoked from the frontend. guest-js/index.ts 
   ```diff
   import { invoke } from '@tauri-apps/api/core'


   export async function ping(value: string): Promise<string | null> {
     return await invoke<{value?: string}>('plugin:test|ping', {
       payload: {
         value,
       },
     }).then((r) => (r.value ? r.value : null));
   }


   +export async function writeCustomFile(user_input: string): Promise<string> {
    +return await invoke('plugin:test|write_custom_file',{userInput: user_input});
   +}
   ```
 Make sure your package is built: 
   ```plaintext
   pnpm build
   ```
 4. ### Define Default Plugin Permissions As our plugin should expose the `write_custom_file` command by default we should add this to our `default.toml` permission. Show solution Add this to our default permission set to allow the new command we just exposed. permissions/default.toml 
   ```toml
   "$schema" = "schemas/schema.json"
   [default]
   description = "Default permissions for the plugin"
   permissions = ["allow-ping", "allow-write-custom-file"]
   ```
 5. ### Invoke Test Command from Example Application The created plugin directory structure contains an `examples/tauri-app` folder, which has a ready to use Tauri application to test out the plugin. Since we added a new command we need to slightly modify the frontend to invoke our new command instead. Show solution src/App.svelte 
   ```diff
   <script>
     import Greet from './lib/Greet.svelte'
     import { ping, writeCustomFile } from 'tauri-plugin-test-api'


     let response = ''


     function updateResponse(returnValue) {
       response += `[${new Date().toLocaleTimeString()}]` + (typeof returnValue === 'string' ? returnValue : JSON.stringify(returnValue)) + '<br>'
     }


     -function _ping() {
       -ping("Pong!").then(updateResponse).catch(updateResponse)
   -  }
     +function _writeCustomFile() {
       +writeCustomFile("HELLO FROM TAURI PLUGIN").then(updateResponse).catch(updateResponse)
   +  }
   </script>


   <main class="container">
     <h1>Welcome to Tauri!</h1>


     <div class="row">
       <a href="https://vitejs.dev" target="_blank">
         <img src="/vite.svg" class="logo vite" alt="Vite Logo" />
       </a>
       <a href="https://tauri.app" target="_blank">
         <img src="/tauri.svg" class="logo tauri" alt="Tauri Logo" />
       </a>
       <a href="https://svelte.dev" target="_blank">
         <img src="/svelte.svg" class="logo svelte" alt="Svelte Logo" />
       </a>
     </div>


     <p>
       Click on the Tauri, Vite, and Svelte logos to learn more.
     </p>


     <div class="row">
       <Greet />
     </div>


     <div>
       <button on:click="{_ping}">Ping</button>
       <div>{@html response}</div>
     </div>
     <div>
       <button on:click="{_writeCustomFile}">Write</button>
       <div>{@html response}</div>
     </div>




   </main>


   <style>
     .logo.vite:hover {
       filter: drop-shadow(0 0 2em #747bff);
     }


     .logo.svelte:hover {
       filter: drop-shadow(0 0 2em #ff3e00);
     }
   </style>
   ```
 Running this and pressing the “Write” button you should be greeted with this: 
   ```plaintext
   success
   ```
 And you should find a `test.txt` file in your temporary folder containing a message from our new implemented plugin command. 🥳

# Node.js as a sidecar

In this guide we are going to package a Node.js application to a self contained binary to be used as a sidecar in a Tauri application without requiring the end user to have a Node.js installation. This example tutorial is applicable for desktop operating systems only. We recommend reading the general [sidecar guide](/develop/sidecar/) first for a deeper understanding of how Tauri sidecars work. ## Goals * Package a Node.js application as a binary. * Integrate this binary as a Tauri sidecar. ## Implementation Details * For this we use the [pkg](https://github.com/yao-pkg/pkg) tool, but any other tool that can compile JavaScript or Typescript into a binary application will work. * You can also embed the Node runtime itself into your Tauri application and ship bundled JavaScript as a resource, but this will ship the JavaScript content as readable-ish files and the runtime is usually larger than a `pkg` packaged application. In this example we will create a Node.js application that reads input from the command line [process.argv](https://nodejs.org/docs/latest/api/process.html#processargv) and writes output to stdout using [console.log](https://nodejs.org/api/console.html#consolelogdata-args).\ You can leverage alternative inter-process communication systems such as a localhost server, stdin/stdout or local sockets. Note that each has their own advantages, drawbacks and security concerns. ## Prerequisites An existing Tauri application set up with the shell plugin, that compiles and runs for you locally. Note Please follow the [shell plugin guide](/plugin/shell/) first to set up and initialize the plugin correctly. Without the plugin being initialized and configured the example won’t work. ## Guide 1. ##### Initialize Sidecar Project Let’s create a new Node.js project to contain our sidecar implementation. Create a new directory **in your Tauri application root folder** (in this example we will call it `sidecar-app`) and run the `init` command of your preferred Node.js package manager inside the directory: * npm 
     ```sh
     npm init
     ```
 * yarn 
     ```sh
     yarn init
     ```
 * pnpm 
     ```sh
     pnpm init
     ```
 We will compile our Node.js application to a self container binary using [pkg](https://github.com/yao-pkg/pkg) among other options. Let’s install it as a development dependency into the new `sidecar-app`: * npm 
     ```sh
     npm add @yao-pkg/pkg --save-dev
     ```
 * yarn 
     ```sh
     yarn add @yao-pkg/pkg --dev
     ```
 * pnpm 
     ```sh
     pnpm add @yao-pkg/pkg --save-dev
     ```
 2. ##### Write Sidecar Logic Now we can start writing JavaScript code that will be executed by our Tauri application. In this example we will process a command from the command line arguments and write output to stdout, which means our process will be short lived and only handle a single command at a time. If your application must be long lived, consider using alternative inter-process communication systems. Let’s create a `index.js` file in our `sidecar-app` directory and write a basic Node.js app: sidecar-app/index.js 
   ```js
   const command = process.argv[2];


   switch (command) {
     case 'hello':
       const message = process.argv[3];
       console.log(`Hello ${message}!`);
       break;
     default:
       console.error(`unknown command ${command}`);
       process.exit(1);
   }
   ```
 3. ##### Package the Sidecar To package our Node.js application into a self contained binary, create a script in `package.json`: sidecar-app/package.json 
   ```json
   {
     "scripts": {
       "build": "pkg index.ts --output my-sidecar"
     }
   }
   ```
 * npm 
     ```sh
     npm run build
     ```
 * yarn 
     ```sh
     yarn build
     ```
 * pnpm 
     ```sh
     pnpm build
     ```
 This will create the `sidecar-app/my-sidecar` binary on Linux and macOS, and a `sidecar-app/my-sidecar.exe` executable on Windows. For sidecar applications, we need to ensure that the binary is named in the correct pattern, for more information read [Embedding External Binaries](/develop/sidecar/) To rename this file to the expected Tauri sidecar filename and also move to our Tauri project, we can use the following Node.js script as a starting example: sidecar-app/rename.js 
   ```js
   import { execSync } from 'child_process';
   import fs from 'fs';


   const ext = process.platform === 'win32' ? '.exe' : '';


   const targetTriple = execSync('rustc --print host-tuple').toString().trim();
   if (!targetTriple) {
     console.error('Failed to determine platform target triple');
   }
   // TODO: create `src-tauri/binaries` dir
   fs.renameSync(
     `my-sidecar${ext}`,
     `../src-tauri/binaries/my-sidecar-${targetTriple}${ext}`
   );
   ```
 Note The `--print host-tuple` flag was added in Rust 1.84.0. If you’re using an older version, you’ll need to parse the output of `rustc -Vv` instead: 
   ```js
   const rustInfo = execSync('rustc -vV');
   const targetTriple = /host: (\S+)/g.exec(rustInfo)[1];
   ```
 And run `node rename.js` from the `sidecar-app` directory. At this step the `/src-tauri/binaries` directory should contain the renamed sidecar binary. 4. ##### Setup plugin-shell permission After installing the [shell plugin](/plugin/shell/) make sure you configure the required capabilities. Note that we use `"args": true` but you can optionally provide an array `["hello"]`, [read more](/develop/sidecar/#passing-arguments). src-tauri/capabilities/default.json 
   ```json
   {
     "permissions": [
       "core:default",
       "opener:default",
       {
         "identifier": "shell:allow-execute",
         "allow": [
           {
             "args": true,
             "name": "binaries/my-sidecar",
             "sidecar": true
           }
         ]
       }
     ]
   }
   ```
 5. ##### Configure the Sidecar in the Tauri Application Now that we have our Node.js application ready, we can connect it to our Tauri application by configuring the [`bundle > externalBin`](/reference/config/#externalbin) array: src-tauri/tauri.conf.json 
   ```json
   {
     "bundle": {
       "externalBin": ["binaries/my-sidecar"]
     }
   }
   ```
 The Tauri CLI will handle the bundling of the sidecar binary as long as it exists as `src-tauri/binaries/my-sidecar-<target-triple>`. 6. ##### Execute the Sidecar We can run the sidecar binary either from Rust code or directly from JavaScript. * JavaScript Let’s execute the `hello` command in the Node.js sidecar directly: 
     ```js
     import { Command } from '@tauri-apps/plugin-shell';


     const message = 'Tauri';


     const command = Command.sidecar('binaries/my-sidecar', ['hello', message]);
     const output = await command.execute();
     // once everything is configured it should log "Hello Tauri" in the browser console.
     console.log(output.stdout)
     ```
 * Rust Let’s pipe a `hello` Tauri command to the Node.js sidecar: 
     ```rust
     use tauri_plugin_shell::ShellExt;


     #[tauri::command]
     async fn hello(app: tauri::AppHandle, cmd: String, message: String) -> String {
         let sidecar_command = app
             .shell()
             .sidecar("my-sidecar")
             .unwrap()
             .arg(cmd)
             .arg(message);
         let output = sidecar_command.output().await.unwrap();
         String::from_utf8(output.stdout).unwrap()
     }
     ```
 Register it in `invoke_handler` and call it in the frontend with: 
     ```js
     import { invoke } from "@tauri-apps/api/core";


     const message = "Tauri"
     console.log(await invoke("hello", { cmd: 'hello', message }))
     ```
 7. ##### Running Lets test it * npm 
     ```sh
     npm run tauri dev
     ```
 * yarn 
     ```sh
     yarn tauri dev
     ```
 * pnpm 
     ```sh
     pnpm tauri dev
     ```
 * deno 
     ```sh
     deno task tauri dev
     ```
 * bun 
     ```sh
     bun tauri dev
     ```
 * cargo 
     ```sh
     cargo tauri dev
     ```
 Open the DevTools with F12 (or `Cmd+Option+I` on macOS) and you should see the output of the sidecar command. If you find any issues, please open an issue on [GitHub](https://github.com/tauri-apps/tauri-docs).

# Splashscreen

In this lab we’ll be implementing a basic splashscreen functionality in a Tauri app. Doing so is quite straight forward, a splashscreen is effectively just a matter of creating a new window that displays some contents during the period your app is doing some heavy setup related tasks and then closing it when setting up is done. ## Prerequisites ## Steps 1. ##### Install dependencies and run the project Before you start developing any project it’s important to build and run the initial template, just to validate your setup is working as intended. Show solution 
   ```sh
   # Make sure you're in the right directory
   cd splashscreen-lab
   # Install dependencies
   pnpm install
   # Build and run the app
   pnpm tauri dev
   ```
 ![Successful run of the created template app.](/_astro/step_1._Ugp-O91_ZSTOi5.webp) 2. ##### Register new windows in `tauri.conf.json` The easiest way of adding new windows is by adding them directly to `tauri.conf.json`. You can also create them dynamically at startup, but for the sake of simplicity lets just register them instead. Make sure you have a window with the label `main` that’s being created as a hidden window and a window with the label `splashscreen` that’s created as being shown directly. You can leave all other options as their defaults, or tweak them based on preference. Show solution src-tauri/tauri.conf.json 
   ```json
   {
       "windows": [
           {
               "label": "main",
               "visible": false
           },
           {
               "label": "splashscreen",
               "url": "/splashscreen"
           }
       ]
   }
   ```
 3. ##### Create a new page to host your splashscreen Before you begin you’ll need to have some content to show. How you develop new pages depend on your chosen framework, most have the concept of a “router” that handles page navigation which should work just like normal in Tauri, in which case you just create a new splashscreen page. Or as we’re going to be doing here, create a new `splashscreen.html` file to host the contents. What’s important here is that you can navigate to a `/splashscreen` URL and be shown the contents you want for your splashscreen. Try running the app again after this step! Show solution /splashscreen.html 
   ```html
   <!doctype html>
   <html lang="en">
   <head>
       <meta charset="UTF-8" />
       <link rel="stylesheet" href="/src/styles.css" />
       <meta name="viewport" content="width=device-width, initial-scale=1.0" />
       <title>Tauri App</title>
   </head>
   <body>
       <div class="container">
           <h1>Tauri used Splash!</h1>
           <div class="row">
               <h5>It was super effective!</h5>
           </div>
       </div>
   </body>
   </html>
   ```
 ![The splashscreen we just created.](/_astro/step_3.Cjc3aTae_Z1m6TK7.webp) 4. ##### Start some setup tasks Since splashscreens are generally intended to be used for the sake of hiding heavy setup related tasks, lets fake giving the app something heavy to do, some in the frontend and some in the backend. To fake heavy setup in the frontend we’re going to be using a simple `setTimeout` function. The easiest way to fake heavy operations in the backend is by using the Tokio crate, which is the Rust crate that Tauri uses in the backend to provide an asynchronous runtime. While Tauri provides the runtime there are various utilities that Tauri doesn’t re-export from it, so we’ll need to add the crate to our project in order to access them. This is a perfectly normal practice within the Rust ecosystem. Don’t use `std::thread::sleep` in async functions, they run cooperatively in a concurrent environment not in parallel, meaning that if you sleep the thread instead of the Tokio task you’ll be locking all tasks scheduled to run on that thread from being executed, causing your app to freeze. Show solution 
   ```sh
   # Run this command where the `Cargo.toml` file is
   cd src-tauri
   # Add the Tokio crate
   cargo add tokio -F time
   # Optionally go back to the top folder to keep developing
   # `tauri dev` can figure out where to run automatically
   cd ..
   ```
 src/main.ts 
   ```javascript
   // These contents can be copy-pasted below the existing code, don't replace the entire file!!


   // Utility function to implement a sleep function in TypeScript
   function sleep(seconds: number): Promise<void> {
       return new Promise(resolve => setTimeout(resolve, seconds * 1000));
   }


   // Setup function
   async function setup() {
       // Fake perform some really heavy setup task
       console.log('Performing really heavy frontend setup task...')
       await sleep(3);
       console.log('Frontend setup task complete!')
       // Set the frontend task as being completed
       invoke('set_complete', {task: 'frontend'})
   }


   // Effectively a JavaScript main function
   window.addEventListener("DOMContentLoaded", () => {
       setup()
   });
   ```
 /src-tauri/src/lib.rs 
   ```rust
   // Import functionalities we'll be using
   use std::sync::Mutex;
   use tauri::async_runtime::spawn;
   use tauri::{AppHandle, Manager, State};
   use tokio::time::{sleep, Duration};


   // Create a struct we'll use to track the completion of
   // setup related tasks
   struct SetupState {
       frontend_task: bool,
       backend_task: bool,
   }


   // Our main entrypoint in a version 2 mobile compatible app
   #[cfg_attr(mobile, tauri::mobile_entry_point)]
   pub fn run() {
       // Don't write code before Tauri starts, write it in the
       // setup hook instead!
       tauri::Builder::default()
           // Register a `State` to be managed by Tauri
           // We need write access to it so we wrap it in a `Mutex`
           .manage(Mutex::new(SetupState {
               frontend_task: false,
               backend_task: false,
           }))
           // Add a command we can use to check
           .invoke_handler(tauri::generate_handler![greet, set_complete])
           // Use the setup hook to execute setup related tasks
           // Runs before the main loop, so no windows are yet created
           .setup(|app| {
               // Spawn setup as a non-blocking task so the windows can be
               // created and ran while it executes
               spawn(setup(app.handle().clone()));
               // The hook expects an Ok result
               Ok(())
           })
           // Run the app
           .run(tauri::generate_context!())
           .expect("error while running tauri application");
   }


   #[tauri::command]
   fn greet(name: String) -> String {
       format!("Hello {name} from Rust!")
   }


   // A custom task for setting the state of a setup task
   #[tauri::command]
   async fn set_complete(
       app: AppHandle,
       state: State<'_, Mutex<SetupState>>,
       task: String,
   ) -> Result<(), ()> {
       // Lock the state without write access
       let mut state_lock = state.lock().unwrap();
       match task.as_str() {
           "frontend" => state_lock.frontend_task = true,
           "backend" => state_lock.backend_task = true,
           _ => panic!("invalid task completed!"),
       }
       // Check if both tasks are completed
       if state_lock.backend_task && state_lock.frontend_task {
           // Setup is complete, we can close the splashscreen
           // and unhide the main window!
           let splash_window = app.get_webview_window("splashscreen").unwrap();
           let main_window = app.get_webview_window("main").unwrap();
           splash_window.close().unwrap();
           main_window.show().unwrap();
       }
       Ok(())
   }


   // An async function that does some heavy setup task
   async fn setup(app: AppHandle) -> Result<(), ()> {
       // Fake performing some heavy action for 3 seconds
       println!("Performing really heavy backend setup task...");
       sleep(Duration::from_secs(3)).await;
       println!("Backend setup task completed!");
       // Set the backend task as being completed
       // Commands can be ran as regular functions as long as you take
       // care of the input arguments yourself
       set_complete(
           app.clone(),
           app.state::<Mutex<SetupState>>(),
           "backend".to_string(),
       )
       .await?;
       Ok(())
   }
   ```
 5. ##### Run the application You should now see a splashscreen window pop up, both the frontend and backend will perform their respective heavy 3 second setup tasks, after which the splashscreen disappears and the main window is shown! ## Discuss ##### Should you have a splashscreen? In general having a splashscreen is an admittance of defeat that you couldn’t make your app load fast enough to not need one. In fact it tends to be better to just go straight to a main window that then shows some little spinner somewhere in a corner informing the user there’s still setup tasks happening in the background. However, with that said, it can be a stylistic choice that you want to have a splashscreen, or you might have some very particular requirement that makes it impossible to start the app until some tasks are performed. It’s definitely not *wrong* to have a splashscreen, it just tends to not be necessary and can make users feel like the app isn’t very well optimized.

# System Tray

Tauri allows you to create and customize a system tray for your application. This can enhance the user experience by providing quick access to common actions. ## Configuration First of all, update your `Cargo.toml` to include the necessary feature for the system tray. src-tauri/Cargo.toml 
```toml
tauri = { version = "2.0.0", features = [ "tray-icon" ] }
```
 ## Usage The tray API is available in both JavaScript and Rust. ### Create a Tray Icon * JavaScript Use the [`TrayIcon.new`](/reference/javascript/api/namespacetray/#new) static function to create a new tray icon: 
  ```javascript
  import { TrayIcon } from '@tauri-apps/api/tray';


  const options = {
    // here you can add a tray menu, title, tooltip, event handler, etc
  };


  const tray = await TrayIcon.new(options);
  ```
 See [`TrayIconOptions`](/reference/javascript/api/namespacetray/#trayiconoptions) for more information on the customization options. * Rust 
  ```rust
  use tauri::tray::TrayIconBuilder;


  tauri::Builder::default()
      .setup(|app| {
          let tray = TrayIconBuilder::new().build(app)?;
          Ok(())
      })
  ```
 See [`TrayIconBuilder`](https://docs.rs/tauri/2.0.0/tauri/tray/struct.TrayIconBuilder.html) for more information on customization options. ### Change the Tray Icon When creating the tray you can use the application icon as the tray icon: * JavaScript 
  ```javascript
  import { TrayIcon } from '@tauri-apps/api/tray';
  import { defaultWindowIcon } from '@tauri-apps/api/app';


  const options = {
    icon: await defaultWindowIcon(),
  };


  const tray = await TrayIcon.new(options);
  ```
 * Rust 
  ```rust
  let tray = TrayIconBuilder::new()
    .icon(app.default_window_icon().unwrap().clone())
    .build(app)?;
  ```
 ### Add a Menu To attach a menu that is displayed when the tray is clicked, you can use the `menu` option. Note By default the menu is displayed on both left and right clicks. To prevent the menu from popping up on left click, call the [`show_menu_on_left_click(false)`](https://docs.rs/tauri/latest/tauri/tray/struct.TrayIconBuilder.html#method.show_menu_on_left_click) Rust function or set the [`menuOnLeftClick`](/reference/javascript/api/namespacetray/#properties-1) JavaScript option to `false`. * JavaScript 
  ```javascript
  import { TrayIcon } from '@tauri-apps/api/tray';
  import { Menu } from '@tauri-apps/api/menu';


  const menu = await Menu.new({
    items: [
      {
        id: 'quit',
        text: 'Quit',
      },
    ],
  });


  const options = {
    menu,
    menuOnLeftClick: true,
  };


  const tray = await TrayIcon.new(options);
  ```
 * Rust 
  ```rust
  use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
  };


  let quit_i = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
  let menu = Menu::with_items(app, &[&quit_i])?;


  let tray = TrayIconBuilder::new()
    .menu(&menu)
    .show_menu_on_left_click(true)
    .build(app)?;
  ```
 #### Listen to Menu Events * JavaScript On JavaScript you can attach a menu click event listener directly to the menu item: * Using a shared menu click handler 
    ```javascript
    import { Menu } from '@tauri-apps/api/menu';


    function onTrayMenuClick(itemId) {
      // itemId === 'quit'
    }


    const menu = await Menu.new({
      items: [
        {
          id: 'quit',
          text: 'Quit',
          action: onTrayMenuClick,
        },
      ],
    });
    ```
 * Using a dedicated menu click handler 
    ```javascript
    import { Menu } from '@tauri-apps/api/menu';


    const menu = await Menu.new({
      items: [
        {
          id: 'quit',
          text: 'Quit',
          action: () => {
            console.log('quit pressed');
          },
        },
      ],
    });
    ```
 * Rust Use the [`TrayIconBuilder::on_menu_event`](https://docs.rs/tauri/2.0.0/tauri/tray/struct.TrayIconBuilder.html#method.on_menu_event) method to attach a tray menu click event listener: 
  ```rust
  use tauri::tray::TrayIconBuilder;


  TrayIconBuilder::new()
    .on_menu_event(|app, event| match event.id.as_ref() {
      "quit" => {
        println!("quit menu item was clicked");
        app.exit(0);
      }
      _ => {
        println!("menu item {:?} not handled", event.id);
      }
    })
  ```
 ### Listen to Tray Events The tray icon emits events for the following mouse events: * click: triggered when the cursor receives a single left, right or middle click, including information on whether the mouse press was released or not * Double click: triggered when the cursor receives a double left, right or middle click * Enter: triggered when the cursor enters the tray icon area * Move: triggered when the cursor moves around the tray icon area * Leave: triggered when the cursor leaves the tray icon area Note Linux: Unsupported. The event is not emitted even though the icon is shown and will still show a context menu on right click. * JavaScript 
  ```javascript
  import { TrayIcon } from '@tauri-apps/api/tray';


  const options = {
    action: (event) => {
      switch (event.type) {
        case 'Click':
          console.log(
            `mouse ${event.button} button pressed, state: ${event.buttonState}`
          );
          break;
        case 'DoubleClick':
          console.log(`mouse ${event.button} button pressed`);
          break;
        case 'Enter':
          console.log(
            `mouse hovered tray at ${event.rect.position.x}, ${event.rect.position.y}`
          );
          break;
        case 'Move':
          console.log(
            `mouse moved on tray at ${event.rect.position.x}, ${event.rect.position.y}`
          );
          break;
        case 'Leave':
          console.log(
            `mouse left tray at ${event.rect.position.x}, ${event.rect.position.y}`
          );
          break;
      }
    },
  };


  const tray = await TrayIcon.new(options);
  ```
 See [`TrayIconEvent`](/reference/javascript/api/namespacetray/#trayiconevent) for more information on the event payload. * Rust 
  ```rust
  use tauri::{
      Manager,
      tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent}
  };


  TrayIconBuilder::new()
    .on_tray_icon_event(|tray, event| match event {
      TrayIconEvent::Click {
        button: MouseButton::Left,
        button_state: MouseButtonState::Up,
        ..
      } => {
        println!("left click pressed and released");
        // in this example, let's show and focus the main window when the tray is clicked
        let app = tray.app_handle();
        if let Some(window) = app.get_webview_window("main") {
          let _ = window.unminimize();
          let _ = window.show();
          let _ = window.set_focus();
        }
      }
      _ => {
        println!("unhandled event {event:?}");
      }
    })
  ```
 See [`TrayIconEvent`](https://docs.rs/tauri/2.0.0/tauri/tray/enum.TrayIconEvent.html) for more information on the event type. For detailed information about creating menus, including menu items, submenus, and dynamic updates, see the [Window Menu](/learn/window-menu/) documentation.

# Window Customization

Tauri provides lots of options for customizing the look and feel of your app’s window. You can create custom titlebars, have transparent windows, enforce size constraints, and more. ## Configuration There are three ways to change the window configuration: * [Through tauri.conf.json](/reference/config/#windowconfig) * [Through the JavaScript API](/reference/javascript/api/namespacewindow/#window) * [Through the Window in Rust](https://docs.rs/tauri/2.0.0/tauri/window/struct.Window.html) ## Usage * [Creating a Custom Titlebar](#creating-a-custom-titlebar) * [(macOS) Transparent Titlebar with Custom Window Background Color](#macos-transparent-titlebar-with-custom-window-background-color) ### Creating a Custom Titlebar A common use of these window features is creating a custom titlebar. This short tutorial will guide you through that process. Note For macOS, using a custom titlebar will also lose some features provided by the system, such as [moving or aligning the window](https://support.apple.com/guide/mac-help/work-with-app-windows-mchlp2469/mac). Another approach to customizing the titlebar but keeping native functions could be making the titlebar transparent and setting the window background color. See the usage [(macOS) Transparent Titlebar with Custom Window Background Color](#macos-transparent-titlebar-with-custom-window-background-color). #### tauri.conf.json Set `decorations` to `false` in your `tauri.conf.json`: tauri.conf.json 
```json
"tauri": {
  "windows": [
    {
      "decorations": false
    }
  ]
}
```
 #### Permissions Add window permissions in capability file. By default, all plugin commands are blocked and cannot be accessed. You must define a list of permissions in your `capabilities` configuration. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    +"core:window:default",
    +"core:window:allow-close",
    +"core:window:allow-minimize",
    +"core:window:allow-toggle-maximize",
    +"core:window:allow-start-dragging"
  ]
}
```
 | Permission | Description | | -------------------------------------------- | ----------------------------------------------------------------------------------------------- | | `core:window:default` | Default permissions for the plugin. This includes `core:window:allow-internal-toggle-maximize`. | | `core:window:allow-close` | Enables the close command without any pre-configured scope. | | `core:window:allow-minimize` | Enables the minimize command without any pre-configured scope. | | `core:window:allow-start-dragging` | Enables the start_dragging command without any pre-configured scope. | | `core:window:allow-toggle-maximize` | Enables the toggle_maximize command without any pre-configured scope. | | `core:window:allow-internal-toggle-maximize` | Enables the internal_toggle_maximize command without any pre-configured scope. | #### CSS Add this CSS sample to keep it at the top of the screen and style the buttons: 
```css
.titlebar {
  height: 30px;
  background: #329ea3;
  user-select: none;
  display: grid;
  grid-template-columns: auto max-content;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
}
.titlebar > .controls {
  display: flex;
}
.titlebar button {
  appearance: none;
  padding: 0;
  margin: 0;
  border: none;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 30px;
  background-color: transparent;
}
.titlebar button:hover {
  background: #5bbec3;
}
```
 #### HTML Put this at the top of your `<body>` tag: 
```html
<div class="titlebar">
  <div data-tauri-drag-region></div>
  <div class="controls">
    <button id="titlebar-minimize" title="minimize">
      <!-- https://api.iconify.design/mdi:window-minimize.svg -->
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
      >
        <path fill="currentColor" d="M19 13H5v-2h14z" />
      </svg>
    </button>
    <button id="titlebar-maximize" title="maximize">
      <!-- https://api.iconify.design/mdi:window-maximize.svg -->
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
      >
        <path fill="currentColor" d="M4 4h16v16H4zm2 4v10h12V8z" />
      </svg>
    </button>
    <button id="titlebar-close" title="close">
      <!-- https://api.iconify.design/mdi:close.svg -->
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="24"
        height="24"
        viewBox="0 0 24 24"
      >
        <path
          fill="currentColor"
          d="M13.46 12L19 17.54V19h-1.46L12 13.46L6.46 19H5v-1.46L10.54 12L5 6.46V5h1.46L12 10.54L17.54 5H19v1.46z"
        />
      </svg>
    </button>
  </div>
</div>
```
 Note that you may need to move the rest of your content down so that the titlebar doesn’t cover it. #### JavaScript Use this code snippet to make the buttons work: 
```javascript
import { getCurrentWindow } from '@tauri-apps/api/window';


// when using `"withGlobalTauri": true`, you may use
// const { getCurrentWindow } = window.__TAURI__.window;


const appWindow = getCurrentWindow();


document
  .getElementById('titlebar-minimize')
  ?.addEventListener('click', () => appWindow.minimize());
document
  .getElementById('titlebar-maximize')
  ?.addEventListener('click', () => appWindow.toggleMaximize());
document
  .getElementById('titlebar-close')
  ?.addEventListener('click', () => appWindow.close());
```
 Note that if you are using a Rust-based frontend, you can copy the code above into a `<script>` element in your `index.html` file. Note `data-tauri-drag-region` will only work on the element to which it is directly applied. If you want the drag behavior to apply to child elements as well, you’ll need to add it to each child individually. This behavior is preserved so that interactive elements like buttons and inputs can function properly. ### Manual Implementation of `data-tauri-drag-region` For use cases where you customize the drag behavior, you can manually add an event listener with `window.startDragging` instead of using `data-tauri-drag-region`. #### HTML From the code in the previous section, we remove `data-tauri-drag-region` and add an `id`: 
```diff
<div data-tauri-drag-region class="titlebar">
  <div id="titlebar" class="titlebar">
    <!-- ... -->
  </div>
</div>
```
 #### Javascript Add an event listener to the titlebar element: 
```js
// ...
document.getElementById('titlebar')?.addEventListener('mousedown', (e) => {
  if (e.buttons === 1) {
    // Primary (left) button
    e.detail === 2
      ? appWindow.toggleMaximize() // Maximize on double click
      : appWindow.startDragging(); // Else start dragging
  }
});
```
 ### (macOS) Transparent Titlebar with Custom Window Background Color We are going to create the main window and change its background color from the Rust side. Remove the main window from the `tauri.conf.json` file: tauri.conf.json 
```diff
"tauri": {
  "windows": [
-    {
      -"title": "Transparent Titlebar Window",
      -"width": 800,
      -"height": 600
-    }
  ],
}
```
 Add `objc2-app-kit` crate to dependencies so that we can use it to call the macOS native API: src-tauri/Cargo.toml 
```toml
[target."cfg(target_os = \"macos\")".dependencies]
objc2-app-kit = { version = "0.3.2", features = ["NSColor", "NSWindow", "objc2-core-foundation"] }
```
 Create the main window and change its background color: src-tauri/src/lib.rs 
```rust
use tauri::{TitleBarStyle, WebviewUrl, WebviewWindowBuilder};


pub fn run() {
  tauri::Builder::default()
    .setup(|app| {
      let win_builder =
        WebviewWindowBuilder::new(app, "main", WebviewUrl::default())
          .title("Transparent Titlebar Window")
          .inner_size(800.0, 600.0);


      // set transparent title bar only when building for macOS
      #[cfg(target_os = "macos")]
      let win_builder = win_builder.title_bar_style(TitleBarStyle::Transparent);


      let window = win_builder.build().unwrap();


      // set background color only when building for macOS
      #[cfg(target_os = "macos")]
      {
        use objc2_app_kit::{NSColor, NSWindow};


        let ns_window_ptr = window.ns_window().unwrap() as *mut NSWindow;
        let ns_window = unsafe { &*ns_window_ptr };
        let bg_color = NSColor::colorWithRed_green_blue_alpha(
          50.0 / 255.0,
          158.0 / 255.0,
          163.5 / 255.0,
          1.0,
        );
        ns_window.setBackgroundColor(Some(&bg_color));
      }


      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
```

# Window Menu

Native application menus can be attached to both to a window or system tray. Available on desktop. ## Creating a base-level menu To create a base-level native window menu, and attach to a window. You can create various types of menu items including basic items, check items, and separators: * JavaScript Use the [`Menu.new`](/reference/javascript/api/namespacemenu/#new-2) static function to create a window menu: 
  ```javascript
  import { Menu } from '@tauri-apps/api/menu';


  await using menu = await Menu.new({
    items: [
      {
        id: 'quit',
        text: 'Quit',
        action: () => {
          console.log('quit pressed');
        },
      },
      {
        id: 'check_item',
        text: 'Check Item',
        checked: true,
      },
      {
        item: 'Separator',
      },
      {
        id: 'disabled_item',
        text: 'Disabled Item',
        enabled: false,
      },
      {
        id: 'status',
        text: 'Status: Processing...',
      },
    ],
  });


  // If a window was not created with an explicit menu or had one set explicitly,
  // this menu will be assigned to it.
  //
  // NOTE: will be empty macOS. On macOS, all top-level entries must be SubMenus.
  await menu.setAsAppMenu();


  // Update individual menu item text
  await using statusItem = await menu.get('status');
  if (statusItem) {
    await statusItem.setText('Status: Ready');
  }
  ```
 * Rust 
  ```rust
  use tauri::menu::MenuBuilder;


  fn main() {
      tauri::Builder::default()
          .setup(|app| {
              // NOTE: will be empty on macOS. On macOS, all top-level entries must be Submenus.
              let menu = MenuBuilder::new(app)
                  .text("open", "Open")
                  .text("close", "Close")
                  .check("check_item", "Check Item")
                  .separator()
                  .text("disabled_item", "Disabled Item")
                  .text("status", "Status: Processing...")
                  .build()?;


              app.set_menu(menu.clone())?;


              // Update individual menu item text
              menu
                  .get("status")
                  .unwrap()
                  .as_menuitem_unchecked()
                  .set_text("Status: Ready")?;


              Ok(())
          })
          .run(tauri::generate_context!())
          .expect("error while running tauri application");
  }
  ```
 ## Listening to events on custom menu items Each custom menu item triggers an event when clicked. Use the `on_menu_event` API to handle them. * JavaScript 
  ```javascript
  import { Menu } from '@tauri-apps/api/menu';


  await using menu = await Menu.new({
    items: [
      {
        id: 'Open',
        text: 'open',
        action: () => {
          console.log('open pressed');
        },
      },
      {
        id: 'Close',
        text: 'close',
        action: () => {
          console.log('close pressed');
        },
      },
    ],
  });


  await menu.setAsAppMenu();
  ```
 * Rust 
  ```rust
  use tauri::menu::MenuBuilder;


  fn main() {
    tauri::Builder::default()
          .setup(|app| {
              let menu = MenuBuilder::new(app)
                  .text("open", "Open")
                  .text("close", "Close")
                  .build()?;


              app.set_menu(menu)?;


              app.on_menu_event(move |app_handle: &tauri::AppHandle, event| {


                  println!("menu event: {:?}", event.id());


                  match event.id().0.as_str() {
                      "open" => {
                          println!("open event");
                      }
                      "close" => {
                          println!("close event");
                      }
                      _ => {
                          println!("unexpected menu event");
                      }
                  }
              });


              Ok(())
          })
          .run(tauri::generate_context!())
          .expect("error while running tauri application");
  }
  ```
 ## Creating a multi-level menu Multi-level menus allow you to group menu items under categories like “File,” “Edit,” etc. These will appear as part of the application window for Windows or Linux, or in the menu bar on MacOS. ![This menu in the macOS menu bar](/_astro/submenus.BXZFbbPm_1Y7k3V.webp) Note On MacOS, all items in an application menu must be grouped under submenus. Top-level items will be ignored: ![An empty macOS menu bar](/_astro/empty.D6Ei_kq7_1B1uSr.webp) Also, the first submenu will *always* become the application’s about menu, regardless of its `text` label. You should include a submenu as the first entry (say, an “About” submenu) to fill this space. In the example, below, “About” is displayed as “tauri-menus”. Note Icon support for submenus is available since Tauri 2.8.0. * JavaScript 
  ```javascript
  import { Menu, Submenu } from '@tauri-apps/api/menu';


  // Will become the application submenu on MacOS
  await using aboutSubmenu = await Submenu.new({
    text: 'About',
    items: [
      {
        id: 'quit',
        text: 'Quit',
        action: () => {
          console.log('Quit pressed');
        },
      },
    ],
  });


  await using fileSubmenu = await Submenu.new({
    text: 'File',
    icon: 'Folder', // Optional: Add an icon to the submenu
    items: [
      {
        id: 'new',
        text: 'New',
        action: () => {
          console.log('New clicked');
        },
      },
      {
        id: 'open',
        text: 'Open',
        action: () => {
          console.log('Open clicked');
        },
      },
      {
        id: 'save_as',
        text: 'Save As...',
        action: () => {
          console.log('Save As clicked');
        },
      },
    ],
  });


  // Note: macOS injects additional "Writing Tools" elements into "Edit" menus
  // (or, failing that, any menu with the "Copy" command).
  await using editSubmenu = await Submenu.new({
    text: 'Edit',
    items: [
      {
        id: 'undo',
        text: 'Undo',
        action: () => {
          console.log('Undo clicked');
        },
      },
      {
        id: 'redo',
        text: 'Redo',
        action: () => {
          console.log('Redo clicked');
        },
      },
    ],
  });


  await using menu = await Menu.new({
    items: [aboutSubmenu, fileSubmenu, editSubmenu],
  });


  await menu.setAsAppMenu();


  // You can also update the submenu icon dynamically
  await fileSubmenu.setIcon('document');
  // Or set a native icon (only one type applies per platform)
  await fileSubmenu.setNativeIcon('NSFolder');
  ```
 * Rust 
  ```rust
  use tauri::{
      image::Image,
      menu::{CheckMenuItemBuilder, IconMenuItemBuilder, MenuBuilder, SubmenuBuilder},
  };


  fn main() {
      tauri::Builder::default()
          .setup(|app| {
              // Will become the application submenu on macOS
              let about_menu = SubmenuBuilder::new(app, "About")
                  .text("quit", "Quit")
                  .build()?;


              let menu_image = Image::from_bytes(include_bytes!("../icons/menu.png")).unwrap();
              let file_menu = SubmenuBuilder::new(app, "File")
                  .submenu_icon(menu_image) // Optional: Add an icon to the submenu
                  .text("open", "Open")
                  .text("quit", "Quit")
                  .build()?;


              let lang_str = "en";
              let check_sub_item_1 = CheckMenuItemBuilder::new("English")
                  .id("en")
                  .checked(lang_str == "en")
                  .build(app)?;


              let check_sub_item_2 = CheckMenuItemBuilder::new("Chinese")
                  .id("zh")
                  .checked(lang_str == "zh")
                  .enabled(false)
                  .build(app)?;


              // Load icon from path
              let icon_image = Image::from_bytes(include_bytes!("../icons/icon.png")).unwrap();


              let icon_item = IconMenuItemBuilder::new("icon")
                  .icon(icon_image)
                  .build(app)?;


              let other_item = SubmenuBuilder::new(app, "language")
                  .item(&check_sub_item_1)
                  .item(&check_sub_item_2)
                  .item(&icon_item)
                  .build()?;


              let menu = MenuBuilder::new(app)
                  .items(&[&about_menu, &file_menu, &other_item])
                  .build()?;


              app.set_menu(menu)?;


              let menu_image_update =
                  Image::from_bytes(include_bytes!("../icons/menu_update.png")).unwrap();
              // You can also update the submenu icon dynamically
              file_menu.set_icon(Some(menu_image_update))?;
              // Or set a native icon (only one type applies per platform)
              file_menu.set_native_icon(Some(tauri::menu::NativeIcon::Folder))?;


              Ok(())
          })
          .run(tauri::generate_context!());
  }
  ```
 Note that you need to enable `image-ico` or `image-png` feature to use this API: src-tauri/Cargo.toml 
  ```toml
  [dependencies]
  tauri = { version = "...", features = ["...", "image-png"] }
  ```
 ## Creating predefined menu To use built-in (native) menu items that has predefined behavior by the operating system or Tauri: * JavaScript 
  ```javascript
  import { Menu, PredefinedMenuItem, Submenu } from '@tauri-apps/api/menu';


  // macOS injects additional "Writing Tools" menu items into your "Edit" menu,
  // or, if that's missing, whichever menu has this copy item:
  await using copy = await PredefinedMenuItem.new({
    text: 'copy-text',
    item: 'Copy',
  });


  await using separator = await PredefinedMenuItem.new({
    text: 'separator-text',
    item: 'Separator',
  });


  await using undo = await PredefinedMenuItem.new({
    text: 'undo-text',
    item: 'Undo',
  });


  await using redo = await PredefinedMenuItem.new({
    text: 'redo-text',
    item: 'Redo',
  });


  await using cut = await PredefinedMenuItem.new({
    text: 'cut-text',
    item: 'Cut',
  });


  await using paste = await PredefinedMenuItem.new({
    text: 'paste-text',
    item: 'Paste',
  });


  await using select_all = await PredefinedMenuItem.new({
    text: 'select_all-text',
    item: 'SelectAll',
  });


  // Becomes the application submenu on MacOS
  await using about = await Submenu.new({ text: 'About', items: [] });


  await using predefined = await Submenu.new({
    text: 'Predefined',
    items: [copy, separator, undo, redo, cut, paste, select_all],
  });


  await using menu = await Menu.new({
    items: [about, predefined],
  });


  await menu.setAsAppMenu();
  ```
 * Rust 
  ```rust
  #![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
  use tauri::menu::{MenuBuilder, PredefinedMenuItem, SubmenuBuilder};


  fn main() {
      tauri::Builder::default()
          .setup(|app| {
              // Becomes the application submenu on macOS
              let about_menu = SubmenuBuilder::new(app, "About").build()?;


              let predefined_menu = SubmenuBuilder::new(app, "Predefined")
                  .copy()
                  .separator()
                  .undo()
                  .redo()
                  .cut()
                  .paste()
                  .select_all()
                  .item(&PredefinedMenuItem::copy(app, Some("custom text"))?)
                  .build()?;


              let menu = MenuBuilder::new(app)
                  .items(&[&about_menu, &predefined_menu])
                  .build()?;
              app.set_menu(menu)?;


              Ok(())
          })
          .run(tauri::generate_context!())
          .expect("error while running tauri application");
  }
  ```
 For more preset capabilities, please refer to the documentation [`PredefinedMenuItem`](https://docs.rs/tauri/latest/tauri/menu/struct.PredefinedMenuItem.html). The result: ![This menu in the macOS menu bar](/_astro/predefined.C6ZKkJgS_Z17u9UB.webp) ## Change menu status If you want to change the status of the menu, such as text, icon, or check status, you can `set_menu` again: * JavaScript 
  ```javascript
  import {
    Menu,
    CheckMenuItem,
    IconMenuItem,
    MenuItem,
    Submenu,
  } from '@tauri-apps/api/menu';
  import { Image } from '@tauri-apps/api/image';


  let currentLanguage = 'en';


  // No `await using`: these items are used inside their `action` callbacks, so must not be freed at end of scope.
  //
  // You must `.close()` them manually later.
  const check_sub_item_en = await CheckMenuItem.new({
    id: 'en',
    text: 'English',
    checked: currentLanguage === 'en',
    action: () => {
      currentLanguage = 'en';
      check_sub_item_en.setChecked(currentLanguage === 'en');
      check_sub_item_zh.setChecked(currentLanguage === 'zh');
      console.log('English pressed');
    },
  });


  const check_sub_item_zh = await CheckMenuItem.new({
    id: 'zh',
    text: 'Chinese',
    checked: currentLanguage === 'zh',
    action: () => {
      currentLanguage = 'zh';
      check_sub_item_en.setChecked(currentLanguage === 'en');
      check_sub_item_zh.setChecked(currentLanguage === 'zh');
      check_sub_item_zh.setAccelerator('Ctrl+L');
      console.log('Chinese pressed');
    },
  });


  // Load icon from path
  await using icon = await Image.fromPath('../src/icon.png');
  const icon2 = await Image.fromPath('../src/icon-2.png');


  const icon_item = await IconMenuItem.new({
    id: 'icon_item',
    text: 'Icon Item',
    icon: icon,
    action: () => {
      icon_item.setIcon(icon2);
      console.log('icon pressed');
    },
  });


  const text_item = await MenuItem.new({
    id: 'text_item',
    text: 'Text Item',
    action: () => {
      text_item.setText('Text Item Changed');
      console.log('text pressed');
    },
  });


  // Becomes the application submenu on MacOS
  await using about = await Submenu.new({ text: 'About', items: [] });


  await using change_menu = await Submenu.new({
    id: 'change_menu',
    text: 'change_menu',
    items: [text_item, check_sub_item_en, check_sub_item_zh, icon_item],
  });


  await using menu = await Menu.new({
    items: [about, change_menu],
  });


  await menu.setAsAppMenu();
  ```
 * Rust 
  ```rust
  // change-menu-status
  #![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]


  use tauri::{
      image::Image,
      menu::{CheckMenuItemBuilder, IconMenuItem, MenuBuilder, MenuItem, SubmenuBuilder},
  };


  fn main() {
      tauri::Builder::default()
          .setup(|app| {
              let check_sub_item_en = CheckMenuItemBuilder::with_id("en", "EN")
                  .checked(true)
                  .build(app)?;


              let check_sub_item_zh = CheckMenuItemBuilder::with_id("zh", "ZH")
                  .checked(false)
                  .build(app)?;


              let text_menu = MenuItem::with_id(
                  app,
                  "change_text",
                  &"Change menu".to_string(),
                  true,
                  Some("Ctrl+Z"),
              )
              .unwrap();


              let icon_menu = IconMenuItem::with_id(
                  app,
                  "change_icon",
                  &"Change icon menu",
                  true,
                  Some(Image::from_bytes(include_bytes!("../icons/icon.png")).unwrap()),
                  Some("Ctrl+F"),
              )
              .unwrap();


              // Becomes the application submenu on macOS
              let about_menu = SubmenuBuilder::new(app, "About").build()?;


              let menu_item = SubmenuBuilder::new(app, "Change menu")
                  .item(&text_menu)
                  .item(&icon_menu)
                  .items(&[&check_sub_item_en, &check_sub_item_zh])
                  .build()?;
              let menu = MenuBuilder::new(app).items(&[&about_menu, &menu_item]).build()?;
              app.set_menu(menu)?;
              app.on_menu_event(move |_app_handle: &tauri::AppHandle, event| {
                  match event.id().0.as_str() {
                      "change_text" => {
                          text_menu
                              .set_text("changed menu text")
                              .expect("Change text error");


                          text_menu
                              .set_text("changed menu text")
                              .expect("Change text error");
                      }
                      "change_icon" => {
                          icon_menu
                              .set_text("changed menu-icon text")
                              .expect("Change text error");
                          icon_menu
                              .set_icon(Some(
                                  Image::from_bytes(include_bytes!("../icons/icon-2.png")).unwrap(),
                              ))
                              .expect("Change icon error");
                      }


                      "en" | "zh" => {
                          check_sub_item_en
                              .set_checked(event.id().0.as_str() == "en")
                              .expect("Change check error");
                          check_sub_item_zh
                              .set_checked(event.id().0.as_str() == "zh")
                              .expect("Change check error");
                          check_sub_item_zh.set_accelerator(Some("Ctrl+L"))
                          .expect("Change accelerator error");
                      }
                      _ => {
                          println!("unexpected menu event");
                      }
                  }
              });


              Ok(())
          })
          .run(tauri::generate_context!())
          .expect("error while running tauri application");
  }
  ```
 The menu looks like this: ![This menu in the macOS menu bar](/_astro/change_menu.B67INHzY_18h2EI.webp) ## Prevent JavaScript menu leaks There’re a few gotchas you should be aware of when using the JavaScript menu APIs, mainly because JavaScript does not have any way to run cleanup code when an object is being removed by garbage collection: * The menus will not clean up automatically unless `close` is called or closed by `await using` after the binding variable goes out of scope. * You should close the menu items you got e.g. from `Menu.get`, the `await using` syntax makes it easier, for example: `await using status = menu.get('status')` Be careful with APIs that can return a `Menu` such as `Menu.setAsAppMenu`, you’ll need to close them when you’re done with them or if you don’t plan to use them. * You should close the menu resource whenever you don’t need to access it in JavaScript anymore. For example: * Manual close 
  ```typescript
  const copy = await PredefinedMenuItem.new({ item: 'Copy' });
  const menu = await Menu.new({ items: [copy] });
  // `copy` is now managed by the `menu` and the JavaScript resource reference can be closed
  await copy.close();


  const prev = await menu.setAsAppMenu();
  // `menu` is now set as the app menu, we can close the JavaScript resource reference
  await menu.close();
  // We don't plan to use the previously set menu, close it here.
  await prev?.close();
  ```
 * await using 
  ```typescript
  await using copy = await PredefinedMenuItem.new({ item: 'Copy' });
  await using menu = await Menu.new({ items: [copy] });
  await using prev = await menu.setAsAppMenu();
  ```

# Features & Recipes

> Information on the extensibility of Tauri from built-in Tauri features and functionality to provided plugins and recipes built by the Tauri community

Tauri comes with extensibility in mind. On this page you’ll find: * **[Official Features](#official-features)**: Built-in Tauri features and functionality * **[Community Resources](#community-plugins)**: More plugins and recipes built by the Tauri community. You can also contribute your own on [Awesome Tauri](https://github.com/tauri-apps/awesome-tauri) * **[Support Table](#support-table)**: A compatibility table showing which platforms are supported by each official plugin **Use the search and filter functionality to find features or community resources:** #### Official Features [Autostart](/plugin/autostart/) Automatically launch your app at system startup. [Barcode Scanner](/plugin/barcode-scanner/) Allows your mobile application to use the camera to scan QR codes, EAN-13 and other types of barcodes. [Biometric](/plugin/biometric/) Prompt the user for biometric authentication on Android and iOS. [Clipboard](/plugin/clipboard/) Read and write to the system clipboard. [Command Line Interface (CLI)](/plugin/cli/) Parse arguments from the command line interface. [Deep Linking](/plugin/deep-linking/) Set your Tauri application as the default handler for an URL. [Dialog](/plugin/dialog/) Native system dialogs for opening and saving files along with message dialogs. [File System](/plugin/file-system/) Access the file system. [Geolocation](/plugin/geolocation/) Get and track the device's current position, including information about altitude, heading, and speed (if available). [Global Shortcut](/plugin/global-shortcut/) Register global shortcuts. [Haptics](/plugin/haptics/) Haptic feedback and vibrations on Android and iOS [HTTP Client](/plugin/http-client/) Access the HTTP client written in Rust. [Localhost](/plugin/localhost/) Use a localhost server in production apps. [Logging](/plugin/logging/) Configurable logging. [NFC](/plugin/nfc/) Read and write NFC tags on Android and iOS. [Notifications](/plugin/notification/) Send native notifications to the user. [Opener](/plugin/opener/) Open files and URLs in external applications. [OS Information](/plugin/os-info/) Read information about the operating system. [Persisted Scope](/plugin/persisted-scope/) Persist runtime scope changes on the filesystem. [Positioner](/plugin/positioner/) Move windows to common locations. [Process](/plugin/process/) Access the current process. [Shell](/plugin/shell/) Access the system shell to spawn child processes. [Single Instance](/plugin/single-instance/) Ensure that a single instance of your Tauri app is running at a time. [SQL](/plugin/sql/) Tauri Plugin providing an interface for the frontend to communicate with SQL databases through sqlx. [Store](/plugin/store/) Persistent key value storage. [Stronghold](/plugin/stronghold/) Encrypted, secure database. [Updater](/plugin/updater/) In-app updates for Tauri applications. [Upload](/plugin/upload/) File uploads through HTTP. [Websocket](/plugin/websocket/) Open a WebSocket connection using a Rust client in JavaScript. [Window State](/plugin/window-state/) Persist window sizes and positions. #### Community Plugins [sentry-tauri](https://github.com/timfish/sentry-tauri)Capture JavaScript errors, Rust panics and native crash minidumps to Sentry. [tauri-awesome-rpc](https://github.com/ahkohd/tauri-awesome-rpc)Custom invoke system that leverages WebSocket. [tauri-nspanel](https://github.com/ahkohd/tauri-nspanel)Convert a window to panel. [tauri-nspopover-plugin](https://github.com/freethinkel/tauri-nspopover-plugin)Native NSPopover view for use in the status bar in macOS. [tauri-plugin-android-battery-optimization](https://github.com/NeoHuncho/tauri-plugin-android-battery-optimization)Check and request battery optimization exemptions on Android. [tauri-plugin-android-fs](https://github.com/aiueo13/tauri-plugin-android-fs)Access the file system on Android. [tauri-plugin-aptabase](https://github.com/aptabase/tauri-plugin-aptabase)Privacy-first and minimalist analytics for desktop and mobile apps. [tauri-plugin-auth](https://github.com/inKibra/tauri-plugins/tree/main/packages/tauri-plugin-auth)Auth plugin for iOS that uses ASWebAuthenticationSession for authentication, which allows keychain access. [tauri-plugin-blec](https://github.com/MnlPhlp/tauri-plugin-blec)Cross platform Bluetooth Low Energy client based on btleplug. [tauri-plugin-cache](https://github.com/Taiizor/tauri-plugin-cache)Advanced disk caching solution with memory layer, TTL management, compression support, and cross-platform compatibility for desktop and mobile. [tauri-plugin-clipboard](https://github.com/CrossCopy/tauri-plugin-clipboard)Clipboard plugin for reading/writing clipboard text/image/html/rtf/files, and monitoring clipboard update. [tauri-plugin-context-menu](https://github.com/c2r0b/tauri-plugin-context-menu)Native context menu. [tauri-plugin-desktop-underlay](https://github.com/Charlie-XIAO/tauri-plugin-desktop-underlay)Attach a window to desktop, below icons and above wallpaper. [tauri-plugin-device-info](https://github.com/edisdev/tauri-plugin-device-info)Access comprehensive device information including battery, network, storage, display, and system details across desktop and mobile. [tauri-plugin-dragout](https://github.com/alexqqqqqq777/tauri-plugin-dragout)Native macOS drag-out (file promise) support. [tauri-plugin-drpc](https://github.com/smokingplaya/tauri-plugin-drpc)Discord RPC support. [tauri-plugin-esc-pos](https://github.com/Kosadchiy/tauri-plugin-esc-pos)ESC/POS receipt printer support over USB and TCP. [tauri-plugin-fs-pro](https://github.com/ayangweb/tauri-plugin-fs-pro)Extended with additional methods for files and directories. [tauri-plugin-graphql](https://github.com/JonasKruckenberg/tauri-plugin-graphql)Type-safe IPC for Tauri using GraphQL. [tauri-plugin-iap](https://github.com/Choochmeque/tauri-plugin-iap)Plugin that enables full In-App Purchases flow for Android, macOS, iOS and Windows. [tauri-plugin-iap](https://github.com/inKibra/tauri-plugins/tree/main/packages/tauri-plugin-iap)In-app-purchase plugin for iOS that allows fetching, purchasing, and restoring of products. [tauri-plugin-in-app-review](https://github.com/Gbyte-Group/tauri-plugin-in-app-review)In-app app rating prompts using native platform APIs. [tauri-plugin-ios-photos](https://github.com/Gbyte-Group/tauri-plugin-ios-photos)iOS Photos album and asset management via native APIs. [tauri-plugin-js](https://github.com/HuakunShen/tauri-plugin-js)Give your app Electron-like JS backends with type-safe RPC powered by kkrpc. Supports Bun, Node.js, and Deno. [tauri-plugin-keep-screen-on](https://gitlab.com/cristofa/tauri-plugin-keep-screen-on)Disable screen timeout on Android and iOS. [tauri-plugin-libsql](https://github.com/HuakunShen/tauri-plugin-libsql)libsql/Turso database support with encryption, embedded replicas, and Drizzle ORM integration. [tauri-plugin-macos-permissions](https://github.com/ayangweb/tauri-plugin-macos-permissions)Support for checking and requesting macOS system permissions. [tauri-plugin-mobile-sharetarget](https://github.com/IT-ess/tauri-plugin-mobile-sharetarget)Handle mobile Share Intents with a FIFO queue [tauri-plugin-mqtt](https://github.com/kuyoonjo/tauri-plugin-mqtt)MQTT client support. [tauri-plugin-network](https://github.com/HuakunShen/tauri-plugin-network)Tools for reading network information and scanning network. [tauri-plugin-nosleep](https://github.com/pevers/tauri-plugin-nosleep/)Block the power save functionality in the OS. [tauri-plugin-ota](https://github.com/inKibra/tauri-plugins/tree/main/packages/tauri-plugin-ota)OTA plugin for applications that just want to continuously deliever new JavaScript code based on a manfiest. [tauri-plugin-pinia](https://github.com/ferreira-tb/tauri-store/tree/main/packages/plugin-pinia)Persistent Pinia stores for Vue. [tauri-plugin-prevent-default](https://github.com/ferreira-tb/tauri-plugin-prevent-default)Disable default browser shortcuts. [tauri-plugin-python](https://github.com/marcomq/tauri-plugin-python/)Use python in your backend. [tauri-plugin-screenshots](https://github.com/ayangweb/tauri-plugin-screenshots)Get screenshots of windows and monitors. [tauri-plugin-serialport](https://github.com/deid84/tauri-plugin-serialport)Cross-compatible serialport communication tool. [tauri-plugin-serialplugin](https://github.com/s00d/tauri-plugin-serialplugin)Cross-compatible serialport communication tool. [tauri-plugin-sharesheet](https://github.com/buildyourwebapp/tauri-plugin-sharesheet)Share content to other apps via the Android Sharesheet or iOS Share Pane. [tauri-plugin-svelte](https://github.com/ferreira-tb/tauri-store/tree/main/packages/plugin-svelte)Persistent Svelte stores. [tauri-plugin-system-info](https://github.com/HuakunShen/tauri-plugin-system-info)Detailed system information. [tauri-plugin-tcp](https://github.com/kuyoonjo/tauri-plugin-tcp)TCP socket support. [tauri-plugin-thermal-printer](https://github.com/luis3132/tauri-plugin-thermal-printer)Add support to handle thermal printers. [tauri-plugin-tracing](https://github.com/fltsci/tauri-plugin-tracing)Structured logging with the tracing crate, featuring JS-to-Rust log bridging, file rotation, and flamegraph profiling. [tauri-plugin-udp](https://github.com/kuyoonjo/tauri-plugin-udp)UDP socket support. [tauri-plugin-velesdb](https://github.com/cyberlife-coder/VelesDB)Native vector database plugin. 70µs semantic search, ≥95% recall, hybrid BM25+vector, offline-first, full ecosystem integrations and more. [tauri-plugin-view](https://github.com/ecmel/tauri-plugin-view)View and share files on mobile. [tauri-plugin-widgets](https://github.com/s00d/tauri-plugin-widgets)Cross-platform home-screen widgets with WidgetKit, AppWidgetManager, Adaptive Cards, and desktop webviews. [tauri-remote-ui](https://github.com/DraviaVemal/tauri-remote-ui)Make you web app bundle available as web page for test and development. [taurpc](https://github.com/MatsDK/TauRPC)Typesafe IPC wrapper for Tauri commands and events. #### Community Integrations [Astrodon](https://github.com/astrodon/astrodon)Make Tauri desktop apps with Deno. [axios-tauri-adapter](https://git.kaki87.net/KaKi87/axios-tauri-adapter)axios adapter for the @tauri-apps/api/http module. [axios-tauri-api-adapter](https://github.com/persiliao/axios-tauri-api-adapter)Makes it easy to use Axios in Tauri, axios adapter for the @tauri-apps/api/http module. [Deno in Tauri](https://github.com/typed-sigterm/deno-in-tauri)Run JS/TS code with Deno Core Engine, in Tauri apps. [faynosync-update-server](https://github.com/ku9nov/faynoSync)Self-hosted Dynamic Update Server with statistics, supporting Tauri and other platforms. Flexible features for seamless app updates and insights. [kkrpc](https://github.com/kunkunsh/kkrpc)Seamless RPC communication between a Tauri app and node/deno/bun processes. [ngx-tauri](https://codeberg.org/crapsilon/ngx-tauri)Small lib to wrap around functions from tauri modules, to integrate easier with Angular. [svelte-tauri-filedrop](https://github.com/probablykasper/svelte-tauri-filedrop)File drop handling component for Svelte. [Tauri Specta](https://github.com/oscartbeaumont/tauri-specta)Completely typesafe Tauri commands. [tauri-htmx-extension](https://github.com/ChristianPavilonis/tauri-htmx-extension)Extention for using htmx with Tauri apis. [tauri-macos-menubar-app-example](https://github.com/ahkohd/tauri-macos-menubar-app-example) [tauri-macos-spotlight-example](https://github.com/ahkohd/tauri-macos-spotlight-example) [tauri-mcp-server](https://github.com/hypothesi/mcp-server-tauri)MCP server and plugin for rapid development and debugging. [tauri-update-cloudflare](https://github.com/mackenly/tauri-update-cloudflare)One-click deploy a Tauri Update Server to Cloudflare. [tauri-update-server](https://git.kaki87.net/KaKi87/tauri-update-server)Automatically interface the Tauri updater with git repository releases. [vite-plugin-tauri](https://github.com/amrbashir/vite-plugin-tauri)Integrate Tauri in a Vite project to build cross-platform apps. ## Support Table Hover “\*” to see notes. For more details, visit the plugin page | Plugin | Rust Version | android | ios | linux | macos | windows | | -------------------- | ------------ | ------- | --- | ----- | ----- | ------- | | autostart | 1.90 | | | | | | | barcode-scanner | 1.90 | | | | | | | biometric | 1.90 | | | | | | | cli | 1.90 | | | | | | | clipboard-manager | 1.90 | \* | \* | | | | | deep-link | 1.90 | \* | \* | | \* | | | dialog | 1.90 | \* | \* | | | | | fs | 1.90 | \* | \* | \* | \* | \* | | geolocation | 1.90 | | | | | | | global-shortcut | 1.90 | | | | | | | haptics | 1.90 | | | | | | | http | 1.90 | | | | | | | localhost | 1.90 | | | | | | | log | 1.90 | | | | | | | nfc | 1.90 | | | | | | | notification | 1.90 | | | | | \* | | opener | 1.90 | \* | \* | | | | | os | 1.90 | | | | | | | persisted-scope | 1.90 | | | | | | | positioner | 1.90 | | | | | | | process | 1.90 | | | | | | | shell | 1.90 | \* | \* | | | | | single-instance | 1.90 | | | | | | | sql | 1.90 | | | | | | | store | 1.90 | | | | | | | stronghold | 1.90 | | | | | | | torch | 1.90 | | | | | | | updater | 1.90 | | | | | | | upload | 1.90 | | | | | | | websocket | 1.90 | | | | | | | window-state | 1.90 | | | | | | | system-tray | 1.90 | | | | | | | window-customization | 1.90 | | | | | |

# Autostart

> Automatically launch your app at system startup.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/autostart)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-autostart)[crates.io](https://crates.io/crates/tauri-plugin-autostart) API Reference:[](/reference/javascript/autostart/)[](https://docs.rs/tauri-plugin-autostart) Automatically launch your application at system startup. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the autostart plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add autostart
    ```
 * yarn 
    ```sh
    yarn run tauri add autostart
    ```
 * pnpm 
    ```sh
    pnpm tauri add autostart
    ```
 * deno 
    ```sh
    deno task tauri add autostart
    ```
 * bun 
    ```sh
    bun tauri add autostart
    ```
 * cargo 
    ```sh
    cargo tauri add autostart
    ```
 * Manual 
  ```sh
  npm run tauri add autostart
  ```
 * npm 
  ```sh
  yarn run tauri add autostart
  ```
 * yarn 
  ```sh
  pnpm tauri add autostart
  ```
 * pnpm 
  ```sh
  deno task tauri add autostart
  ```
 * deno 
  ```sh
  bun tauri add autostart
  ```
 * bun 
  ```sh
  cargo tauri add autostart
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-autostart --target 'cfg(any(target_os = "macos", windows, target_os = "linux"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(desktop)]
                 +app.handle().plugin(tauri_plugin_autostart::init(tauri_plugin_autostart::MacosLauncher::LaunchAgent, Some(vec!["--flag1", "--flag2"]) /* arbitrary number of args to pass to your app */));
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. You can install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-autostart
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-autostart
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-autostart
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-autostart
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-autostart
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-autostart
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-autostart
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-autostart
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-autostart
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-autostart
  ```
 ## Usage The autostart plugin is available in both JavaScript and Rust. * JavaScript 
  ```javascript
  import { enable, isEnabled, disable } from '@tauri-apps/plugin-autostart';
  // when using `"withGlobalTauri": true`, you may use
  // const { enable, isEnabled, disable } = window.__TAURI__.autostart;


  // Enable autostart
  await enable();
  // Check enable state
  console.log(`registered for autostart? ${await isEnabled()}`);
  // Disable autostart
  disable();
  ```
 * Rust 
  ```rust
  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
      tauri::Builder::default()
          .setup(|app| {
              #[cfg(desktop)]
              {
                  use tauri_plugin_autostart::MacosLauncher;
                  use tauri_plugin_autostart::ManagerExt;


                  app.handle().plugin(tauri_plugin_autostart::init(
                      MacosLauncher::LaunchAgent,
                      Some(vec!["--flag1", "--flag2"]),
                  ));


                  // Get the autostart manager
                  let autostart_manager = app.autolaunch();
                  // Enable autostart
                  let _ = autostart_manager.enable();
                  // Check enable state
                  println!("registered for autostart? {}", autostart_manager.is_enabled().unwrap());
                  // Disable autostart
                  let _ = autostart_manager.disable();
              }
              Ok(())
          })
          .run(tauri::generate_context!())
          .expect("error while running tauri application");
  }
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```json
{
  "permissions": [
    ...,
    "autostart:allow-enable",
    "autostart:allow-disable",
    "autostart:allow-is-enabled"
  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures if your application can enable or disable auto starting the application on boot. #### [Granted Permissions](#granted-permissions) It allows all to check, enable and disable the automatic start on boot. #### This default permission set includes the following: * `allow-enable` * `allow-disable` * `allow-is-enabled` ## Permission Table | Identifier | Description | | ---------------------------- | ---------------------------------------------------------------- | | `autostart:allow-disable` | Enables the disable command without any pre-configured scope. | | `autostart:deny-disable` | Denies the disable command without any pre-configured scope. | | `autostart:allow-enable` | Enables the enable command without any pre-configured scope. | | `autostart:deny-enable` | Denies the enable command without any pre-configured scope. | | `autostart:allow-is-enabled` | Enables the is_enabled command without any pre-configured scope. | | `autostart:deny-is-enabled` | Denies the is_enabled command without any pre-configured scope. |

# Barcode Scanner

> Allows your mobile application to use the camera to scan QR codes, EAN-13 and other types of barcodes.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/barcode-scanner)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-barcode-scanner)[crates.io](https://crates.io/crates/tauri-plugin-barcode-scanner) API Reference:[](/reference/javascript/barcode-scanner/)[](https://docs.rs/tauri-plugin-barcode-scanner) Allows your mobile application to use the camera to scan QR codes, EAN-13 and other kinds of barcodes. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the barcode-scanner plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add barcode-scanner
    ```
 * yarn 
    ```sh
    yarn run tauri add barcode-scanner
    ```
 * pnpm 
    ```sh
    pnpm tauri add barcode-scanner
    ```
 * deno 
    ```sh
    deno task tauri add barcode-scanner
    ```
 * bun 
    ```sh
    bun tauri add barcode-scanner
    ```
 * cargo 
    ```sh
    cargo tauri add barcode-scanner
    ```
 * Manual 
  ```sh
  npm run tauri add barcode-scanner
  ```
 * npm 
  ```sh
  yarn run tauri add barcode-scanner
  ```
 * yarn 
  ```sh
  pnpm tauri add barcode-scanner
  ```
 * pnpm 
  ```sh
  deno task tauri add barcode-scanner
  ```
 * deno 
  ```sh
  bun tauri add barcode-scanner
  ```
 * bun 
  ```sh
  cargo tauri add barcode-scanner
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-barcode-scanner --target 'cfg(any(target_os = "android", target_os = "ios"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(mobile)]
                 +app.handle().plugin(tauri_plugin_barcode_scanner::init());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-barcode-scanner
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-barcode-scanner
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-barcode-scanner
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-barcode-scanner
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-barcode-scanner
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-barcode-scanner
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-barcode-scanner
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-barcode-scanner
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-barcode-scanner
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-barcode-scanner
  ```
 ## Configuration On iOS the barcode scanner plugin requires the `NSCameraUsageDescription` information property list value, which should describe why your app needs to use the camera. In the `src-tauri/Info.ios.plist` file, add the following snippet: src-tauri/Info.ios.plist 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>NSCameraUsageDescription</key>
    <string>Read QR codes</string>
  </dict>
</plist>
```
 ## Usage The barcode scanner plugin is available in JavaScript. 
```javascript
import { scan, Format } from '@tauri-apps/plugin-barcode-scanner';
// when using `"withGlobalTauri": true`, you may use
// const { scan, Format } = window.__TAURI__.barcodeScanner;


// `windowed: true` actually sets the webview to transparent
// instead of opening a separate view for the camera
// make sure your user interface is ready to show what is underneath with a transparent element
scan({ windowed: true, formats: [Format.QRCode] });
```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/mobile.json 
```json
{
  "$schema": "../gen/schemas/mobile-schema.json",
  "identifier": "mobile-capability",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": ["barcode-scanner:allow-scan", "barcode-scanner:allow-cancel"]
}
```
 ## [Default Permission](#default-permission) This permission set configures which barcode scanning features are by default exposed. #### [Granted Permissions](#granted-permissions) It allows all barcode related features. #### This default permission set includes the following: * `allow-cancel` * `allow-check-permissions` * `allow-open-app-settings` * `allow-request-permissions` * `allow-scan` * `allow-vibrate` ## Permission Table | Identifier | Description | | ------------------------------------------- | ------------------------------------------------------------------------- | | `barcode-scanner:allow-cancel` | Enables the cancel command without any pre-configured scope. | | `barcode-scanner:deny-cancel` | Denies the cancel command without any pre-configured scope. | | `barcode-scanner:allow-check-permissions` | Enables the check_permissions command without any pre-configured scope. | | `barcode-scanner:deny-check-permissions` | Denies the check_permissions command without any pre-configured scope. | | `barcode-scanner:allow-open-app-settings` | Enables the open_app_settings command without any pre-configured scope. | | `barcode-scanner:deny-open-app-settings` | Denies the open_app_settings command without any pre-configured scope. | | `barcode-scanner:allow-request-permissions` | Enables the request_permissions command without any pre-configured scope. | | `barcode-scanner:deny-request-permissions` | Denies the request_permissions command without any pre-configured scope. | | `barcode-scanner:allow-scan` | Enables the scan command without any pre-configured scope. | | `barcode-scanner:deny-scan` | Denies the scan command without any pre-configured scope. | | `barcode-scanner:allow-vibrate` | Enables the vibrate command without any pre-configured scope. | | `barcode-scanner:deny-vibrate` | Denies the vibrate command without any pre-configured scope. |

# Biometric

> Prompt the user for biometric authentication on Android and iOS.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/biometric)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-biometric)[crates.io](https://crates.io/crates/tauri-plugin-biometric) API Reference:[](/reference/javascript/biometric/)[](https://docs.rs/tauri-plugin-biometric) Prompt the user for biometric authentication on Android and iOS. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the biometric plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add biometric
    ```
 * yarn 
    ```sh
    yarn run tauri add biometric
    ```
 * pnpm 
    ```sh
    pnpm tauri add biometric
    ```
 * deno 
    ```sh
    deno task tauri add biometric
    ```
 * bun 
    ```sh
    bun tauri add biometric
    ```
 * cargo 
    ```sh
    cargo tauri add biometric
    ```
 * Manual 
  ```sh
  npm run tauri add biometric
  ```
 * npm 
  ```sh
  yarn run tauri add biometric
  ```
 * yarn 
  ```sh
  pnpm tauri add biometric
  ```
 * pnpm 
  ```sh
  deno task tauri add biometric
  ```
 * deno 
  ```sh
  bun tauri add biometric
  ```
 * bun 
  ```sh
  cargo tauri add biometric
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-biometric --target 'cfg(any(target_os = "android", target_os = "ios"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(mobile)]
                 +app.handle().plugin(tauri_plugin_biometric::Builder::new().build());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-biometric
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-biometric
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-biometric
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-biometric
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-biometric
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-biometric
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-biometric
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-biometric
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-biometric
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-biometric
  ```
 ## Configuration On iOS the biometric plugin requires the `NSFaceIDUsageDescription` information property list value, which should describe why your app needs to use biometric authentication. In the `src-tauri/Info.ios.plist` file, add the following snippet: src-tauri/Info.ios.plist 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>NSFaceIDUsageDescription</key>
    <string>Authenticate with biometric</string>
  </dict>
</plist>
```
 ## Usage This plugin enables you to verify the availability of Biometric Authentication on a device, prompt the user for biometric authentication, and check the result to determine if the authentication was successful or not. ### Check Status You can check the status of Biometric Authentication, including its availability and the types of biometric authentication methods supported. * JavaScript 
  ```javascript
  import { checkStatus } from '@tauri-apps/plugin-biometric';


  const status = await checkStatus();
  if (status.isAvailable) {
    console.log('Yes! Biometric Authentication is available');
  } else {
    console.log(
      'No! Biometric Authentication is not available due to ' + status.error
    );
  }
  ```
 * Rust 
  ```rust
  use tauri_plugin_biometric::BiometricExt;


  fn check_biometric(app_handle: tauri::AppHandle) {
      let status = app_handle.biometric().status().unwrap();
      if status.is_available {
          println!("Yes! Biometric Authentication is available");
      } else {
          println!("No! Biometric Authentication is not available due to: {}", status.error.unwrap());
      }
  }
  ```
 ### Authenticate To prompt the user for Biometric Authentication, utilize the `authenticate()` method. * JavaScript 
  ```diff
  import { authenticate } from '@tauri-apps/plugin-biometric';


  const options = {
    // Set true if you want the user to be able to authenticate using phone password
    allowDeviceCredential: false,
    cancelTitle: "Feature won't work if Canceled",


    // iOS only feature
    fallbackTitle: 'Sorry, authentication failed',


    // Android only features
    title: 'Tauri feature',
    subtitle: 'Authenticate to access the locked Tauri function',
    confirmationRequired: true,
  };


  try {
    +await authenticate('This feature is locked', options);
    console.log(
      'Hooray! Successfully Authenticated! We can now perform the locked Tauri function!'
    );
  } catch (err) {
    console.log('Oh no! Authentication failed because ' + err.message);
  }
  ```
 * Rust 
  ```diff
  use tauri_plugin_biometric::{BiometricExt, AuthOptions};


  fn bio_auth(app_handle: tauri::AppHandle) {


      let options = AuthOptions {
          // Set True if you want the user to be able to authenticate using phone password
          allow_device_credential:false,
          cancel_title: Some("Feature won't work if Canceled".to_string()),


          // iOS only feature
          fallback_title: Some("Sorry, authentication failed".to_string()),


          // Android only features
          title: Some("Tauri feature".to_string()),
          subtitle: Some("Authenticate to access the locked Tauri function".to_string()),
          confirmation_required: Some(true),
      };


      // if the authentication was successful, the function returns Result::Ok()
      // otherwise returns Result::Error()
      +match app_handle.biometric().authenticate("This feature is locked".to_string(), options) {
          Ok(_) => {
              println!("Hooray! Successfully Authenticated! We can now perform the locked Tauri function!");
          }
          Err(e) => {
              println!("Oh no! Authentication failed because : {e}");
          }
      }
  }
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  +"permissions": ["biometric:default"]
}
```
 ## [Default Permission](#default-permission) This permission set configures which biometric features are by default exposed. #### [Granted Permissions](#granted-permissions) It allows checking the biometric status and prompting for authentication. Encrypting and decrypting data with `biometric_cipher` is not included and must be enabled explicitly with `biometric:allow-biometric-cipher`. #### This default permission set includes the following: * `allow-authenticate` * `allow-status` ## Permission Table | Identifier | Description | | ---------------------------------- | ---------------------------------------------------------------------- | | `biometric:allow-authenticate` | Enables the authenticate command without any pre-configured scope. | | `biometric:deny-authenticate` | Denies the authenticate command without any pre-configured scope. | | `biometric:allow-biometric-cipher` | Enables the biometric_cipher command without any pre-configured scope. | | `biometric:deny-biometric-cipher` | Denies the biometric_cipher command without any pre-configured scope. | | `biometric:allow-status` | Enables the status command without any pre-configured scope. | | `biometric:deny-status` | Denies the status command without any pre-configured scope. |

# Command Line Interface (CLI)

> Parse arguments from the command line interface.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/cli)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-cli)[crates.io](https://crates.io/crates/tauri-plugin-cli) API Reference:[](/reference/javascript/cli/)[](https://docs.rs/tauri-plugin-cli) Tauri enables your app to have a CLI through [clap](https://github.com/clap-rs/clap), a robust command line argument parser. With a simple CLI definition in your `tauri.conf.json` file, you can define your interface and read its argument matches map on JavaScript and/or Rust. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | * Windows * Due to an OS limitation, production apps are not able to write text back to the calling console by default. Please check out [tauri#8305](https://github.com/tauri-apps/tauri/issues/8305#issuecomment-1826871949) for a workaround. ## Setup Install the CLI plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add cli
    ```
 * yarn 
    ```sh
    yarn run tauri add cli
    ```
 * pnpm 
    ```sh
    pnpm tauri add cli
    ```
 * deno 
    ```sh
    deno task tauri add cli
    ```
 * bun 
    ```sh
    bun tauri add cli
    ```
 * cargo 
    ```sh
    cargo tauri add cli
    ```
 * Manual 
  ```sh
  npm run tauri add cli
  ```
 * npm 
  ```sh
  yarn run tauri add cli
  ```
 * yarn 
  ```sh
  pnpm tauri add cli
  ```
 * pnpm 
  ```sh
  deno task tauri add cli
  ```
 * deno 
  ```sh
  bun tauri add cli
  ```
 * bun 
  ```sh
  cargo tauri add cli
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-cli --target 'cfg(any(target_os = "macos", windows, target_os = "linux"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(desktop)]
                 +app.handle().plugin(tauri_plugin_cli::init());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-cli
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-cli
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-cli
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-cli
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-cli
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-cli
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-cli
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-cli
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-cli
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-cli
  ```
 ## Base Configuration Under `tauri.conf.json`, you have the following structure to configure the interface: src-tauri/tauri.conf.json 
```json
{
  "plugins": {
    "cli": {
      "description": "Tauri CLI Plugin Example",
      "args": [
        {
          "short": "v",
          "name": "verbose",
          "description": "Verbosity level"
        }
      ],
      "subcommands": {
        "run": {
          "description": "Run the application",
          "args": [
            {
              "name": "debug",
              "description": "Run application in debug mode"
            },
            {
              "name": "release",
              "description": "Run application in release mode"
            }
          ]
        }
      }
    }
  }
}
```
 Note All JSON configurations here are just samples, many other fields have been omitted for the sake of clarity. ## Adding Arguments The `args` array represents the list of arguments accepted by its command or subcommand. ### Positional Arguments A positional argument is identified by its position in the list of arguments. With the following configuration: src-tauri/tauri.conf.json 
```json
{
  "args": [
    {
      "name": "source",
      "index": 1,
      "takesValue": true
    },
    {
      "name": "destination",
      "index": 2,
      "takesValue": true
    }
  ]
}
```
 Users can run your app as `./app tauri.txt dest.txt` and the arg matches map will define `source` as `"tauri.txt"` and `destination` as `"dest.txt"`. ### Named Arguments A named argument is a (key, value) pair where the key identifies the value. With the following configuration: tauri-src/tauri.conf.json 
```json
{
  "args": [
    {
      "name": "type",
      "short": "t",
      "takesValue": true,
      "multiple": true,
      "possibleValues": ["foo", "bar"]
    }
  ]
}
```
 Users can run your app as `./app --type foo bar`, `./app -t foo -t bar` or `./app --type=foo,bar` and the arg matches map will define `type` as `["foo", "bar"]`. ### Flag Arguments A flag argument is a standalone key whose presence or absence provides information to your application. With the following configuration: tauri-src/tauri.conf.json 
```json
{
  "args": [
    {
      "name": "verbose",
      "short": "v"
    }
  ]
}
```
 Users can run your app as `./app -v -v -v`, `./app --verbose --verbose --verbose` or `./app -vvv` and the arg matches map will define `verbose` as `true`, with `occurrences = 3`. ## Subcommands Some CLI applications have additional interfaces as subcommands. For instance, the `git` CLI has `git branch`, `git commit` and `git push`. You can define additional nested interfaces with the `subcommands` array: tauri-src/tauri.conf.json 
```json
{
  "cli": {
    ...
    "subcommands": {
      "branch": {
        "args": []
      },
      "push": {
        "args": []
      }
    }
  }
}
```
 Its configuration is the same as the root application configuration, with the `description`, `longDescription`, `args`, etc. ## Usage The CLI plugin is available in both JavaScript and Rust. * JavaScript 
  ```javascript
  import { getMatches } from '@tauri-apps/plugin-cli';
  // when using `"withGlobalTauri": true`, you may use
  // const { getMatches } = window.__TAURI__.cli;


  const matches = await getMatches();
  if (matches.subcommand?.name === 'run') {
    // `./your-app run $ARGS` was executed
    const args = matches.subcommand.matches.args;
    if (args.debug?.value === true) {
      // `./your-app run --debug` was executed
    }
    if (args.release?.value === true) {
      // `./your-app run --release` was executed
    }
  }
  ```
 * Rust src-tauri/src/lib.rs 
  ```rust
  use tauri_plugin_cli::CliExt;


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
     tauri::Builder::default()
         .plugin(tauri_plugin_cli::init())
         .setup(|app| {
             match app.cli().matches() {
                 // `matches` here is a Struct with { args, subcommand }.
                 // `args` is `HashMap<String, ArgData>` where `ArgData` is a struct with { value, occurrences }.
                 // `subcommand` is `Option<Box<SubcommandMatches>>` where `SubcommandMatches` is a struct with { name, matches }.
                 Ok(matches) => {
                     println!("{:?}", matches)
                 }
                 Err(_) => {}
             }
             Ok(())
         })
         .run(tauri::generate_context!())
         .expect("error while running tauri application");
  }
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  +"permissions": ["cli:default"]
}
```
 ## [Default Permission](#default-permission) Allows reading the CLI matches #### This default permission set includes the following: * `allow-cli-matches` ## Permission Table | Identifier | Description | | ----------------------- | ----------------------------------------------------------------- | | `cli:allow-cli-matches` | Enables the cli_matches command without any pre-configured scope. | | `cli:deny-cli-matches` | Denies the cli_matches command without any pre-configured scope. |

# Clipboard

> Read and write to the system clipboard.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/clipboard-manager)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-clipboard-manager)[crates.io](https://crates.io/crates/tauri-plugin-clipboard-manager) API Reference:[](/reference/javascript/clipboard-manager/)[](https://docs.rs/tauri-plugin-clipboard-manager) Read and write to the system clipboard using the clipboard plugin. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ------------------------------- | | windows | | | | linux | | | | macos | | | | android | | Only plain-text content support | | ios | | Only plain-text content support | ## Setup Install the clipboard plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add clipboard-manager
    ```
 * yarn 
    ```sh
    yarn run tauri add clipboard-manager
    ```
 * pnpm 
    ```sh
    pnpm tauri add clipboard-manager
    ```
 * deno 
    ```sh
    deno task tauri add clipboard-manager
    ```
 * bun 
    ```sh
    bun tauri add clipboard-manager
    ```
 * cargo 
    ```sh
    cargo tauri add clipboard-manager
    ```
 * Manual 
  ```sh
  npm run tauri add clipboard-manager
  ```
 * npm 
  ```sh
  yarn run tauri add clipboard-manager
  ```
 * yarn 
  ```sh
  pnpm tauri add clipboard-manager
  ```
 * pnpm 
  ```sh
  deno task tauri add clipboard-manager
  ```
 * deno 
  ```sh
  bun tauri add clipboard-manager
  ```
 * bun 
  ```sh
  cargo tauri add clipboard-manager
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-clipboard-manager
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_clipboard_manager::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. If you’d like to manage the clipboard in JavaScript then install the npm package as well: * npm 
       ```sh
       npm install @tauri-apps/plugin-clipboard-manager
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-clipboard-manager
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-clipboard-manager
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-clipboard-manager
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-clipboard-manager
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-clipboard-manager
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-clipboard-manager
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-clipboard-manager
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-clipboard-manager
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-clipboard-manager
  ```
 ## Usage The clipboard plugin is available in both JavaScript and Rust. * JavaScript 
  ```javascript
  import { writeText, readText } from '@tauri-apps/plugin-clipboard-manager';
  // when using `"withGlobalTauri": true`, you may use
  // const { writeText, readText } = window.__TAURI__.clipboardManager;


  // Write content to clipboard
  await writeText('Tauri is awesome!');


  // Read content from clipboard
  const content = await readText();
  console.log(content);
  // Prints "Tauri is awesome!" to the console
  ```
 * Rust 
  ```rust
  use tauri_plugin_clipboard_manager::ClipboardExt;


  app.clipboard().write_text("Tauri is awesome!".to_string()).unwrap();


  // Read content from clipboard
  let content = app.clipboard().read_text();
  println!("{:?}", content.unwrap());
  // Prints "Tauri is awesome!" to the terminal
  ```
 ## [Default Permission](#default-permission) No features are enabled by default, as we believe the clipboard can be inherently dangerous and it is application specific if read and/or write access is needed. Clipboard interaction needs to be explicitly enabled. ## Permission Table | Identifier | Description | | -------------------------------------- | ------------------------------------------------------------------ | | `clipboard-manager:allow-clear` | Enables the clear command without any pre-configured scope. | | `clipboard-manager:deny-clear` | Denies the clear command without any pre-configured scope. | | `clipboard-manager:allow-read-image` | Enables the read_image command without any pre-configured scope. | | `clipboard-manager:deny-read-image` | Denies the read_image command without any pre-configured scope. | | `clipboard-manager:allow-read-text` | Enables the read_text command without any pre-configured scope. | | `clipboard-manager:deny-read-text` | Denies the read_text command without any pre-configured scope. | | `clipboard-manager:allow-write-html` | Enables the write_html command without any pre-configured scope. | | `clipboard-manager:deny-write-html` | Denies the write_html command without any pre-configured scope. | | `clipboard-manager:allow-write-image` | Enables the write_image command without any pre-configured scope. | | `clipboard-manager:deny-write-image` | Denies the write_image command without any pre-configured scope. | | `clipboard-manager:allow-write-secret` | Enables the write_secret command without any pre-configured scope. | | `clipboard-manager:deny-write-secret` | Denies the write_secret command without any pre-configured scope. | | `clipboard-manager:allow-write-text` | Enables the write_text command without any pre-configured scope. | | `clipboard-manager:deny-write-text` | Denies the write_text command without any pre-configured scope. |

# Deep Linking

> Set your Tauri application as the default handler for an URL.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/deep-link)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-deep-link)[crates.io](https://crates.io/crates/tauri-plugin-deep-link) API Reference:[](/reference/javascript/deep-link/)[](https://docs.rs/tauri-plugin-deep-link) Set your Tauri application as the default handler for an URL. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ------------------------------------------------------------------------------------------ | | windows | | | | linux | | | | macos | | Deep links must be registered in config. Dynamic registration at runtime is not supported. | | android | | Deep links must be registered in config. Dynamic registration at runtime is not supported. | | ios | | Deep links must be registered in config. Dynamic registration at runtime is not supported. | ## Setup Install the deep-link plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add deep-link
    ```
 * yarn 
    ```sh
    yarn run tauri add deep-link
    ```
 * pnpm 
    ```sh
    pnpm tauri add deep-link
    ```
 * deno 
    ```sh
    deno task tauri add deep-link
    ```
 * bun 
    ```sh
    bun tauri add deep-link
    ```
 * cargo 
    ```sh
    cargo tauri add deep-link
    ```
 * Manual 
  ```sh
  npm run tauri add deep-link
  ```
 * npm 
  ```sh
  yarn run tauri add deep-link
  ```
 * yarn 
  ```sh
  pnpm tauri add deep-link
  ```
 * pnpm 
  ```sh
  deno task tauri add deep-link
  ```
 * deno 
  ```sh
  bun tauri add deep-link
  ```
 * bun 
  ```sh
  cargo tauri add deep-link
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-deep-link@2.0.0
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_deep_link::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-deep-link
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-deep-link
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-deep-link
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-deep-link
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-deep-link
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-deep-link
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-deep-link
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-deep-link
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-deep-link
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-deep-link
  ```
 ## Setting up ### Android There are two ways to open your app from links on Android: 1. **App Links (http/https + host, verified)** For [app links](https://developer.android.com/training/app-links#android-app-links), you need a server with a `.well-known/assetlinks.json` endpoint that must return a text response in the given format: .well-known/assetlinks.json 
```json
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "$APP_BUNDLE_ID",
      "sha256_cert_fingerprints": [
        $CERT_FINGERPRINT
      ]
    }
  }
]
```
 Where `$APP_BUNDLE_ID` is the value defined on [`tauri.conf.json > identifier`](/reference/config/#identifier) with `-` replaced with `_` and `$CERT_FINGERPRINT` is a list of SHA256 fingerprints of your app’s signing certificates, see [verify Android applinks](https://developer.android.com/training/app-links/verify-android-applinks#web-assoc) for more information. 2. **Custom URI schemes (no host required, no verification)** For URIs like `myapp://...`, you can declare a custom scheme without hosting any files. Use the `scheme` field in the mobile configuration and omit the `host`. ### iOS There are two ways to open your app from links on iOS: 1. **Universal Links (https + host, verified)** For [universal links](https://developer.apple.com/documentation/xcode/allowing-apps-and-websites-to-link-to-your-content?language=objc), you need a server with a `.well-known/apple-app-site-association` endpoint that must return a JSON response in the given format: .well-known/apple-app-site-association 
```json
{
  "applinks": {
    "details": [
      {
        "appIDs": ["$DEVELOPMENT_TEAM_ID.$APP_BUNDLE_ID"],
        "components": [
          {
            "/": "/open/*",
            "comment": "Matches any URL whose path starts with /open/"
          }
        ]
      }
    ]
  }
}
```
 Note The response `Content-Type` header must be `application/json`. The `.well-known/apple-app-site-association` endpoint must be served over HTTPS. To test localhost you can either use a self-signed TLS certificate and install it on the iOS simulator or use services like [ngrok](https://ngrok.com/). Where `$DEVELOPMENT_TEAM_ID` is the value defined on `tauri.conf.json > bundle > iOS > developmentTeam` or the `TAURI_APPLE_DEVELOPMENT_TEAM` environment variable and `$APP_BUNDLE_ID` is the value defined on [`tauri.conf.json > identifier`](/reference/config/#identifier). To verify if your domain has been properly configured to expose the app associations, you can run the following command, replacing `<host>` with your actual host: 
```sh
curl -v https://app-site-association.cdn-apple.com/a/v1/<host>
```
 See [applinks.details](https://developer.apple.com/documentation/bundleresources/applinks/details-swift.dictionary) for more information. 2. **Custom URI schemes (no host, no verification)** For URIs like `myapp://...`, you can declare a custom scheme under mobile configuration with `"appLink": false` (or omit it). The plugin generates the appropriate `CFBundleURLTypes` entries in your app’s Info.plist. No `.well-known` files or HTTPS host are needed. ### Desktop On Linux and Windows deep links are delivered as a command line argument to a new app process. The deep link plugin has integration with the [single instance](/plugin/single-instance/) plugin if you prefer having a unique app instance receiving the events. * First you must add the `deep-link` feature to the single instance plugin: src-tauri/Cargo.toml 
```toml
[target."cfg(any(target_os = \"macos\", windows, target_os = \"linux\"))".dependencies]
tauri-plugin-single-instance = { version = "2.0.0", features = ["deep-link"] }
```
 * Then configure the single instance plugin which should always be the first plugin you register: src-tauri/lib.rs 
```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();


    #[cfg(desktop)]
    {
        builder = builder.plugin(tauri_plugin_single_instance::init(|_app, argv, _cwd| {
          println!("a new app instance was opened with {argv:?} and the deep link event was already triggered");
          // when defining deep link schemes at runtime, you must also check `argv` here
        }));
    }


    builder = builder.plugin(tauri_plugin_deep_link::init());
}
```
 Caution The user could trigger a fake deep link manually by including the URL as argument. Tauri matches the command line argument against the configured schemes to mitigate this, but you should still check if the URL matches the format you expect. This means Tauri only handles deep links for schemes that were statically configured, and schemes registered at runtime must be manually checked using [`Env::args_os`](https://docs.rs/tauri/2.0.0/tauri/struct.Env.html#structfield.args_os). ## Configuration Under `tauri.conf.json > plugins > deep-link`, configure mobile domains/schemes and desktop schemes you want to associate with your application. ### Examples **Custom scheme on mobile (no server required):** tauri.conf.json 
```json
{
  "plugins": {
    "deep-link": {
      "mobile": [
        {
          "scheme": ["ovi"],
          "appLink": false
        }
      ]
    }
  }
}
```
 This registers the `ovi://*` scheme on Android and iOS. **App Link / Universal Link (verified https + host):** 
```json
{
  "plugins": {
    "deep-link": {
      "mobile": [
        {
          "scheme": ["https"],
          "host": "your.website.com",
          "pathPrefix": ["/open"],
          "appLink": true
        }
      ]
    }
  }
}
```
 This registers `https://your.website.com/open/*` as an app/universal link. **Desktop custom schemes:** 
```json
{
  "plugins": {
    "deep-link": {
      "desktop": {
        "schemes": ["something", "my-tauri-app"]
      }
    }
  }
}
```
 ## Usage The deep-link plugin is available in both JavaScript and Rust. ### Listening to Deep Links * JavaScript When a deep link triggers your app while it’s running, the `onOpenUrl` callback is called. To detect whether your app was opened via a deep link, use `getCurrent` on app start. 
  ```javascript
  import { getCurrent, onOpenUrl } from '@tauri-apps/plugin-deep-link';
  // when using `"withGlobalTauri": true`, you may use
  // const { getCurrent, onOpenUrl } = window.__TAURI__.deepLink;


  const startUrls = await getCurrent();
  if (startUrls) {
    // App was likely started via a deep link
    // Note that getCurrent's return value will also get updated every time onOpenUrl gets triggered.
  }


  await onOpenUrl((urls) => {
    console.log('deep link:', urls);
  });
  ```
 * Rust When a deep link triggers your app while it’s running, the plugin’s `on_open_url` closure is called. To detect whether your app was opened via a deep link, use `get_current` on app start. src-tauri/src/lib.rs 
  ```rust
  use tauri_plugin_deep_link::DeepLinkExt;


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
      tauri::Builder::default()
          .plugin(tauri_plugin_deep_link::init())
          .setup(|app| {
              // Note that get_current's return value will also get updated every time on_open_url gets triggered.
              let start_urls = app.deep_link().get_current()?;
              if let Some(urls) = start_urls {
                  // app was likely started by a deep link
                  println!("deep link URLs: {:?}", urls);
              }


              app.deep_link().on_open_url(|event| {
                  println!("deep link URLs: {:?}", event.urls());
              });
              Ok(())
          })
          .run(tauri::generate_context!())
          .expect("error while running tauri application");
  }
  ```
 Note The open URL event is triggered with a list of URLs that were requested to be compatible with the macOS API for deep links, but in most cases your app will only receive a single URL. ### Registering Desktop Deep Links at Runtime The [configuration](#configuration) section describes how to define static deep link schemes for your application. On Linux and Windows it is possible to also associate schemes with your application at runtime via the `register` Rust function. In the following snippet, we will register the `my-app` scheme at runtime. After executing the app for the first time, the operating system will open `my-app://*` URLs with our application: src-tauri/src/lib.rs 
```rust
use tauri_plugin_deep_link::DeepLinkExt;


#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_deep_link::init())
        .setup(|app| {
            #[cfg(desktop)]
            app.deep_link().register("my-app")?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```
 Note Registering the deep links at runtime can be useful for developing on Linux and Windows as by default the deep link is only registered when your app is installed. Installing an AppImage can be complicated as it requires an AppImage launcher. Registering the deep links at runtime might be preferred, so Tauri also includes a helper function to force register all statically configured deep links at runtime. Calling this function also ensures the deep links is registered for development mode: 
```rust
#[cfg(any(target_os = "linux", all(debug_assertions, windows)))]
{
  use tauri_plugin_deep_link::DeepLinkExt;
  app.deep_link().register_all()?;
}
```
 ## Testing There are some caveats to test deep links for your application. ### Desktop Deep links are only triggered for installed applications on desktop. On Linux and Windows you can circumvent this using the [`register_all`](https://docs.rs/tauri-plugin-deep-link/2.0.0/tauri_plugin_deep_link/struct.DeepLink.html#method.register_all) Rust function, which registers all configured schemes to trigger the current executable: src-tauri/src/lib.rs 
```rust
use tauri_plugin_deep_link::DeepLinkExt;


#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_deep_link::init())
        .setup(|app| {
            #[cfg(any(windows, target_os = "linux"))]
            {
                use tauri_plugin_deep_link::DeepLinkExt;
                app.deep_link().register_all()?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```
 Note Installing an AppImage that supports deep links on Linux requires an AppImage launcher to integrate the AppImage with the operating system. Using the `register_all` function you can support deep links out of the box, without requiring your users to use external tools. When the AppImage is moved to a different location in the file system, the deep link is invalidated since it leverages an absolute path to the executable, which makes registering the schemes at runtime even more important. See the [Registering Desktop Deep Links at Runtime](#registering-desktop-deep-links-at-runtime) section for more information. Caution Registering deep links at runtime is not possible on macOS, so deep links can only be tested on the bundled application, which must be installed in the `/Applications` directory. #### Windows To trigger a deep link on Windows you can either open `<scheme>://url` in the browser or run the following command in the terminal: 
```sh
start <scheme>://url
```
 #### Linux To trigger a deep link on Linux you can either open `<scheme>://url` in the browser or run `xdg-open` in the terminal: 
```sh
xdg-open <scheme>://url
```
 ### iOS To trigger an app link on iOS you can open the `https://<host>/path` URL in the browser. For simulators you can leverage the `simctl` CLI to directly open a link from the terminal: 
```sh
xcrun simctl openurl booted https://<host>/path
```
 ### Android To trigger an app link on Android you can open the `https://<host>/path` URL in the browser. For emulators you can leverage the `adb` CLI to directly open a link from the terminal: 
```sh
adb shell am start -a android.intent.action.VIEW -d https://<host>/path <bundle-identifier>
```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/mobile-schema.json",
  "identifier": "mobile-capability",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": [
    // Usually you will need core:event:default to listen to the deep-link event
    "core:event:default",
    +"deep-link:default"
  ]
}
```
 ## [Default Permission](#default-permission) Allows reading the opened deep link via the get_current command #### This default permission set includes the following: * `allow-get-current` ## Permission Table | Identifier | Description | | ------------------------------- | ------------------------------------------------------------------- | | `deep-link:allow-get-current` | Enables the get_current command without any pre-configured scope. | | `deep-link:deny-get-current` | Denies the get_current command without any pre-configured scope. | | `deep-link:allow-is-registered` | Enables the is_registered command without any pre-configured scope. | | `deep-link:deny-is-registered` | Denies the is_registered command without any pre-configured scope. | | `deep-link:allow-register` | Enables the register command without any pre-configured scope. | | `deep-link:deny-register` | Denies the register command without any pre-configured scope. | | `deep-link:allow-unregister` | Enables the unregister command without any pre-configured scope. | | `deep-link:deny-unregister` | Denies the unregister command without any pre-configured scope. |

# Dialog

> Native system dialogs for opening and saving files along with message dialogs.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/dialog)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-dialog)[crates.io](https://crates.io/crates/tauri-plugin-dialog) API Reference:[](/reference/javascript/dialog/)[](https://docs.rs/tauri-plugin-dialog) Native system dialogs for opening and saving files along with message dialogs. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ------------------------------ | | windows | | | | linux | | | | macos | | | | android | | Does not support folder picker | | ios | | Does not support folder picker | ## Setup Install the dialog plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add dialog
    ```
 * yarn 
    ```sh
    yarn run tauri add dialog
    ```
 * pnpm 
    ```sh
    pnpm tauri add dialog
    ```
 * deno 
    ```sh
    deno task tauri add dialog
    ```
 * bun 
    ```sh
    bun tauri add dialog
    ```
 * cargo 
    ```sh
    cargo tauri add dialog
    ```
 * Manual 
  ```sh
  npm run tauri add dialog
  ```
 * npm 
  ```sh
  yarn run tauri add dialog
  ```
 * yarn 
  ```sh
  pnpm tauri add dialog
  ```
 * pnpm 
  ```sh
  deno task tauri add dialog
  ```
 * deno 
  ```sh
  bun tauri add dialog
  ```
 * bun 
  ```sh
  cargo tauri add dialog
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-dialog
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_dialog::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. If you’d like create dialogs in JavaScript, install the npm package as well: * npm 
       ```sh
       npm install @tauri-apps/plugin-dialog
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-dialog
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-dialog
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-dialog
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-dialog
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-dialog
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-dialog
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-dialog
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-dialog
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-dialog
  ```
 ## Usage The dialog plugin is available in both JavaScript and Rust. Here’s how you can use it: in JavaScript: * [Create Yes/No Dialog](#create-yesno-dialog) * [Create Ok/Cancel Dialog](#create-okcancel-dialog) * [Create Message Dialog](#create-message-dialog) * [Open a File Selector Dialog](#open-a-file-selector-dialog) * [Save to File Dialog](#save-to-file-dialog) in Rust: * [Build an Ask Dialog](#build-an-ask-dialog) * [Build a Message Dialog](#build-a-message-dialog) * [Build a File Selector Dialog](#build-a-file-selector-dialog) Note The file dialog APIs returns file system paths on Linux, Windows and macOS. On iOS, a `file://<path>` URIs are returned. On Android, [content URIs](https://developer.android.com/guide/topics/providers/content-provider-basics) are returned. The [filesystem plugin](/plugin/file-system/) works with any path format out of the box. ### JavaScript See all [Dialog Options](/reference/javascript/dialog/) at the JavaScript API reference. #### Create Yes/No Dialog Shows a question dialog with `Yes` and `No` buttons. 
```javascript
import { ask } from '@tauri-apps/plugin-dialog';
// when using `"withGlobalTauri": true`, you may use
// const { ask } = window.__TAURI__.dialog;


// Create a Yes/No dialog
const answer = await ask('This action cannot be reverted. Are you sure?', {
  title: 'Tauri',
  kind: 'warning',
});


console.log(answer);
// Prints boolean to the console
```
 #### Create Ok/Cancel Dialog Shows a question dialog with `Ok` and `Cancel` buttons. 
```javascript
import { confirm } from '@tauri-apps/plugin-dialog';
// when using `"withGlobalTauri": true`, you may use
// const { confirm } = window.__TAURI__.dialog;


// Creates a confirmation Ok/Cancel dialog
const confirmation = await confirm(
  'This action cannot be reverted. Are you sure?',
  { title: 'Tauri', kind: 'warning' }
);


console.log(confirmation);
// Prints boolean to the console
```
 #### Create Message Dialog Shows a message dialog with an `Ok` button. Keep in mind that if the user closes the dialog it will return `false`. 
```javascript
import { message } from '@tauri-apps/plugin-dialog';
// when using `"withGlobalTauri": true`, you may use
// const { message } = window.__TAURI__.dialog;


// Shows message
await message('File not found', { title: 'Tauri', kind: 'error' });
```
 #### Open a File Selector Dialog Open a file/directory selection dialog. The `multiple` option controls whether the dialog allows multiple selection or not, while the `directory`, whether is a directory selection or not. 
```javascript
import { open } from '@tauri-apps/plugin-dialog';
// when using `"withGlobalTauri": true`, you may use
// const { open } = window.__TAURI__.dialog;


// Open a dialog
const file = await open({
  multiple: false,
  directory: false,
});
console.log(file);
// Prints file path or URI
```
 #### Save to File Dialog Open a file/directory save dialog. 
```javascript
import { save } from '@tauri-apps/plugin-dialog';
// when using `"withGlobalTauri": true`, you may use
// const { save } = window.__TAURI__.dialog;


// Prompt to save a 'My Filter' with extension .png or .jpeg
const path = await save({
  filters: [
    {
      name: 'My Filter',
      extensions: ['png', 'jpeg'],
    },
  ],
});
console.log(path);
// Prints the chosen path
```
 *** ### Rust Refer to the [Rust API reference](https://docs.rs/tauri-plugin-dialog/) to see all available options. #### Build an Ask Dialog Shows a question dialog with `Absolutely` and `Totally` buttons. 
```rust
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons};


let answer = app.dialog()
        .message("Tauri is Awesome")
        .title("Tauri is Awesome")
        .buttons(MessageDialogButtons::OkCancelCustom("Absolutely", "Totally"))
        .blocking_show();
```
 If you need a non blocking operation you can use `show()` instead: 
```rust
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons};


app.dialog()
    .message("Tauri is Awesome")
    .title("Tauri is Awesome")
   .buttons(MessageDialogButtons::OkCancelCustom("Absolutely", "Totally"))
    .show(|result| match result {
        true => // do something,
        false =>// do something,
    });
```
 #### Build a Message Dialog Shows a message dialog with an `Ok` button. Keep in mind that if the user closes the dialog it will return `false`. 
```rust
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};


let ans = app.dialog()
    .message("File not found")
    .kind(MessageDialogKind::Error)
    .title("Warning")
    .blocking_show();
```
 If you need a non blocking operation you can use `show()` instead: 
```rust
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons, MessageDialogKind};


app.dialog()
    .message("Tauri is Awesome")
    .kind(MessageDialogKind::Info)
    .title("Information")
    .buttons(MessageDialogButtons::OkCustom("Absolutely"))
    .show(|result| match result {
        true => // do something,
        false => // do something,
    });
```
 #### Build a File Selector Dialog #### Pick Files 
```rust
use tauri_plugin_dialog::DialogExt;


let file_path = app.dialog().file().blocking_pick_file();
// return a file_path `Option`, or `None` if the user closes the dialog
```
 If you need a non blocking operation you can use `pick_file()` instead: 
```rust
use tauri_plugin_dialog::DialogExt;


app.dialog().file().pick_file(|file_path| {
    // return a file_path `Option`, or `None` if the user closes the dialog
    })
```
 #### Save Files 
```rust
use tauri_plugin_dialog::DialogExt;


let file_path = app
    .dialog()
    .file()
    .add_filter("My Filter", &["png", "jpeg"])
    .blocking_save_file();
    // do something with the optional file path here
    // the file path is `None` if the user closed the dialog
```
 or, alternatively: 
```rust
use tauri_plugin_dialog::DialogExt;


app.dialog()
    .file()
    .add_filter("My Filter", &["png", "jpeg"])
    .pick_file(|file_path| {
        // return a file_path `Option`, or `None` if the user closes the dialog
    });
```
 ## [Default Permission](#default-permission) This permission set configures the types of dialogs available from the dialog plugin. #### [Granted Permissions](#granted-permissions) All dialog types are enabled. #### This default permission set includes the following: * `allow-message` * `allow-save` * `allow-open` ## Permission Table | Identifier | Description | | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | | `dialog:allow-ask` | Enables the ask command without any pre-configured scope. (**DEPRECATED**: This is now an alias to `allow-message` and will be removed in v3) | | `dialog:deny-ask` | Denies the ask command without any pre-configured scope. (**DEPRECATED**: This is now an alias to `deny-message` and will be removed in v3) | | `dialog:allow-message` | Enables the message command without any pre-configured scope. | | `dialog:deny-message` | Denies the message command without any pre-configured scope. | | `dialog:allow-open` | Enables the open command without any pre-configured scope. | | `dialog:deny-open` | Denies the open command without any pre-configured scope. | | `dialog:allow-save` | Enables the save command without any pre-configured scope. | | `dialog:deny-save` | Denies the save command without any pre-configured scope. | | `dialog:allow-confirm` | Enables the confirm command without any pre-configured scope. (**DEPRECATED**: This is now an alias to `allow-message` and will be removed in v3) | | `dialog:deny-confirm` | Denies the confirm command without any pre-configured scope. (**DEPRECATED**: This is now an alias to `deny-message` and will be removed in v3) |

# File System

> Access the file system.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/fs)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-fs)[crates.io](https://crates.io/crates/tauri-plugin-fs) API Reference:[](/reference/javascript/fs/)[](https://docs.rs/tauri-plugin-fs) Access the file system. Use std::fs or tokio::fs on the Rust side If you want to manipulate files/directories through Rust, use traditional Rust’s libs (std::fs, tokio::fs, etc). ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | -------------------------------------------------------------------------------------------------------------------------------- | | windows | | Apps installed via MSI or NSIS in `perMachine` and `both` mode require admin permissions for write access in `$RESOURCES` folder | | linux | | No write access to `$RESOURCES` folder | | macos | | No write access to `$RESOURCES` folder | | android | | Access is restricted to Application folder by default | | ios | | Access is restricted to Application folder by default | ## Setup Install the fs plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add fs
    ```
 * yarn 
    ```sh
    yarn run tauri add fs
    ```
 * pnpm 
    ```sh
    pnpm tauri add fs
    ```
 * deno 
    ```sh
    deno task tauri add fs
    ```
 * bun 
    ```sh
    bun tauri add fs
    ```
 * cargo 
    ```sh
    cargo tauri add fs
    ```
 * Manual 
  ```sh
  npm run tauri add fs
  ```
 * npm 
  ```sh
  yarn run tauri add fs
  ```
 * yarn 
  ```sh
  pnpm tauri add fs
  ```
 * pnpm 
  ```sh
  deno task tauri add fs
  ```
 * deno 
  ```sh
  bun tauri add fs
  ```
 * bun 
  ```sh
  cargo tauri add fs
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-fs
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
       tauri::Builder::default()
         +.plugin(tauri_plugin_fs::init())
         .run(tauri::generate_context!())
         .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-fs
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-fs
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-fs
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-fs
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-fs
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-fs
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-fs
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-fs
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-fs
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-fs
  ```
 ## Configuration ### Android When using the audio, cache, documents, downloads, picture, public or video directories your app must have access to the external storage. Include the following permissions to the `manifest` tag in the `gen/android/app/src/main/AndroidManifest.xml` file: 
```xml
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```
 ### iOS Apple requires app developers to specify approved reasons for API usage to enhance user privacy. You must create a `PrivacyInfo.xcprivacy` file in the `src-tauri/gen/apple` folder with the required [NSPrivacyAccessedAPICategoryFileTimestamp](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api#4278393) key and the [C617.1](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api#4278393) recommended reason. 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>NSPrivacyAccessedAPITypes</key>
    <array>
      <dict>
        <key>NSPrivacyAccessedAPIType</key>
        <string>NSPrivacyAccessedAPICategoryFileTimestamp</string>
        <key>NSPrivacyAccessedAPITypeReasons</key>
        <array>
          <string>C617.1</string>
        </array>
      </dict>
    </array>
  </dict>
</plist>
```
 ## Usage The fs plugin is available in both JavaScript and Rust. Different APIs Although this plugin has a file manipulation API on the frontend, in the backend it offers only the methods to change permission of some resources (files, directories, etc). In the Rust side you can use the traditional file manipulation libraries, [std::fs](https://doc.rust-lang.org/std/fs/struct.File.html), [tokio::fs](https://docs.rs/tokio/latest/tokio/fs/index.html) or others. * JavaScript 
  ```javascript
  import { exists, BaseDirectory } from '@tauri-apps/plugin-fs';
  // when using `"withGlobalTauri": true`, you may use
  // const { exists, BaseDirectory } = window.__TAURI__.fs;


  // Check if the `$APPDATA/avatar.png` file exists
  await exists('avatar.png', { baseDir: BaseDirectory.AppData });
  ```
 * Rust src-tauri/src/lib.rs 
  ```rust
  use tauri_plugin_fs::FsExt;


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            // allowed the given directory
            let scope = app.fs_scope();
            scope.allow_directory("/path/to/directory", false);
            dbg!(scope.allowed());


            Ok(())
         })
         .run(tauri::generate_context!())
         .expect("error while running tauri application");
  }
  ```
 ## Security This module prevents path traversal, not allowing parent directory accessors to be used (i.e. “/usr/path/to/../file” or “../path/to/file” paths are not allowed). Paths accessed with this API must be either relative to one of the [base directories](/reference/javascript/api/namespacepath/#basedirectory) or created with the [path API](/reference/javascript/api/namespacepath/). See [@tauri-apps/plugin-fs - Security](/reference/javascript/fs/#security) for more information. ## Paths The file system plugin offers two ways of manipulating paths: the [base directory](/reference/javascript/api/namespacepath/#basedirectory) and the [path API](/reference/javascript/api/namespacepath/). * base directory Every API has an options argument that lets you define a [baseDir](/reference/javascript/api/namespacepath/#basedirectory) that acts as the working directory of the operation. 
  ```js
  import { readFile } from '@tauri-apps/plugin-fs';
  const contents = await readFile('avatars/tauri.png', {
    baseDir: BaseDirectory.Home,
  });
  ```
 In the above example the \~/avatars/tauri.png file is read since we are using the **Home** base directory. * path API Alternatively you can use the path APIs to perform path manipulations. 
  ```js
  import { readFile } from '@tauri-apps/plugin-fs';
  import * as path from '@tauri-apps/api/path';
  const home = await path.homeDir();
  const contents = await readFile(await path.join(home, 'avatars/tauri.png'));
  ```
 ## Files ### Create Creates a file and returns a handle to it. If the file already exists, it is truncated. 
```js
import { create, BaseDirectory } from '@tauri-apps/plugin-fs';
const file = await create('foo/bar.txt', { baseDir: BaseDirectory.AppData });
await file.write(new TextEncoder().encode('Hello world'));
await file.close();
```
 Note Always call `file.close()` when you are done manipulating the file. ### Write The plugin offers separate APIs for writing text and binary files for performance. * text files 
  ```js
  import { writeTextFile, BaseDirectory } from '@tauri-apps/plugin-fs';
  const contents = JSON.stringify({ notifications: true });
  await writeTextFile('config.json', contents, {
    baseDir: BaseDirectory.AppConfig,
  });
  ```
 * binary files 
  ```js
  import { writeFile, BaseDirectory } from '@tauri-apps/plugin-fs';
  const contents = new Uint8Array(); // fill a byte array
  await writeFile('config', contents, {
    baseDir: BaseDirectory.AppConfig,
  });
  ```
 ### Open Opens a file and returns a handle to it. With this API you have more control over how the file should be opened (read-only mode, write-only mode, append instead of overwrite, only create if it does not exist, etc). Note Always call `file.close()` when you are done manipulating the file. * read-only This is the default mode. 
  ```js
  import { open, BaseDirectory } from '@tauri-apps/plugin-fs';
  const file = await open('foo/bar.txt', {
    read: true,
    baseDir: BaseDirectory.AppData,
  });


  const stat = await file.stat();
  const buf = new Uint8Array(stat.size);
  await file.read(buf);
  const textContents = new TextDecoder().decode(buf);
  await file.close();
  ```
 * write-only 
  ```js
  import { open, BaseDirectory } from '@tauri-apps/plugin-fs';
  const file = await open('foo/bar.txt', {
    write: true,
    baseDir: BaseDirectory.AppData,
  });
  await file.write(new TextEncoder().encode('Hello world'));
  await file.close();
  ```
 By default the file is truncated on any `file.write()` call. See the following example to learn how to append to the existing contents instead. * append 
  ```js
  import { open, BaseDirectory } from '@tauri-apps/plugin-fs';
  const file = await open('foo/bar.txt', {
    append: true,
    baseDir: BaseDirectory.AppData,
  });
  await file.write(new TextEncoder().encode('world'));
  await file.close();
  ```
 Note that `{ append: true }` has the same effect as `{ write: true, append: true }`. * truncate When the `truncate` option is set and the file already exists, it will be truncated to length 0. 
  ```js
  import { open, BaseDirectory } from '@tauri-apps/plugin-fs';
  const file = await open('foo/bar.txt', {
    write: true,
    truncate: true,
    baseDir: BaseDirectory.AppData,
  });
  await file.write(new TextEncoder().encode('world'));
  await file.close();
  ```
 This option requires `write` to be `true`. You can use it along the `append` option if you want to rewrite an existing file using multiple `file.write()` calls. * create By default the `open` API only opens existing files. To create the file if it does not exist, opening it if it does, set `create` to `true`: 
  ```js
  import { open, BaseDirectory } from '@tauri-apps/plugin-fs';
  const file = await open('foo/bar.txt', {
    write: true,
    create: true,
    baseDir: BaseDirectory.AppData,
  });
  await file.write(new TextEncoder().encode('world'));
  await file.close();
  ```
 In order for the file to be created, `write` or `append` must also be set to `true`. To fail if the file already exists, see `createNew`. * createNew `createNew` works similarly to `create`, but will fail if the file already exists. 
  ```js
  import { open, BaseDirectory } from '@tauri-apps/plugin-fs';
  const file = await open('foo/bar.txt', {
    write: true,
    createNew: true,
    baseDir: BaseDirectory.AppData,
  });
  await file.write(new TextEncoder().encode('world'));
  await file.close();
  ```
 In order for the file to be created, `write` must also be set to `true`. ### Read The plugin offers separate APIs for reading text and binary files for performance. * text files 
  ```js
  import { readTextFile, BaseDirectory } from '@tauri-apps/plugin-fs';
  const configToml = await readTextFile('config.toml', {
    baseDir: BaseDirectory.AppConfig,
  });
  ```
 If the file is large you can stream its lines with the `readTextFileLines` API: 
  ```typescript
  import { readTextFileLines, BaseDirectory } from '@tauri-apps/plugin-fs';
  const lines = await readTextFileLines('app.logs', {
    baseDir: BaseDirectory.AppLog,
  });
  for await (const line of lines) {
    console.log(line);
  }
  ```
 * binary files 
  ```js
  import { readFile, BaseDirectory } from '@tauri-apps/plugin-fs';
  const icon = await readFile('icon.png', {
    baseDir: BaseDirectory.Resources,
  });
  ```
 ### Remove Call `remove()` to delete a file. If the file does not exist, an error is returned. 
```js
import { remove, BaseDirectory } from '@tauri-apps/plugin-fs';
await remove('user.db', { baseDir: BaseDirectory.AppLocalData });
```
 ### Copy The `copyFile` function takes the source and destination paths. Note that you must configure each base directory separately. 
```js
import { copyFile, BaseDirectory } from '@tauri-apps/plugin-fs';
await copyFile('user.db', 'user.db.bk', {
  fromPathBaseDir: BaseDirectory.AppLocalData,
  toPathBaseDir: BaseDirectory.Temp,
});
```
 In the above example the \<app-local-data>/user.db file is copied to $TMPDIR/user.db.bk. ### Exists Use the `exists()` function to check if a file exists: 
```js
import { exists, BaseDirectory } from '@tauri-apps/plugin-fs';
const tokenExists = await exists('token', {
  baseDir: BaseDirectory.AppLocalData,
});
```
 ### Metadata File metadata can be retrieved with the `stat` and the `lstat` functions. `stat` follows symlinks (and returns an error if the actual file it points to is not allowed by the scope) and `lstat` does not follow symlinks, returning the information of the symlink itself. 
```js
import { stat, BaseDirectory } from '@tauri-apps/plugin-fs';
const metadata = await stat('app.db', {
  baseDir: BaseDirectory.AppLocalData,
});
```
 ### Rename The `rename` function takes the source and destination paths. Note that you must configure each base directory separately. 
```js
import { rename, BaseDirectory } from '@tauri-apps/plugin-fs';
await rename('user.db.bk', 'user.db', {
  fromPathBaseDir: BaseDirectory.AppLocalData,
  toPathBaseDir: BaseDirectory.Temp,
});
```
 In the above example the \<app-local-data>/user.db.bk file is renamed to $TMPDIR/user.db. ### Truncate Truncates or extends the specified file to reach the specified file length (defaults to 0). * truncate to 0 length 
```typescript
import { truncate } from '@tauri-apps/plugin-fs';
await truncate('my_file.txt', 0, { baseDir: BaseDirectory.AppLocalData });
```
 * truncate to a specific length 
```typescript
import {
  truncate,
  readTextFile,
  writeTextFile,
  BaseDirectory,
} from '@tauri-apps/plugin-fs';


const filePath = 'file.txt';
await writeTextFile(filePath, 'Hello World', {
  baseDir: BaseDirectory.AppLocalData,
});
await truncate(filePath, 7, {
  baseDir: BaseDirectory.AppLocalData,
});
const data = await readTextFile(filePath, {
  baseDir: BaseDirectory.AppLocalData,
});
console.log(data); // "Hello W"
```
 ## Directories ### Create To create a directory, call the `mkdir` function: 
```js
import { mkdir, BaseDirectory } from '@tauri-apps/plugin-fs';
await mkdir('images', {
  baseDir: BaseDirectory.AppLocalData,
});
```
 ### Read The `readDir` function recursively lists the entries of a directory: 
```typescript
import { readDir, BaseDirectory } from '@tauri-apps/plugin-fs';
const entries = await readDir('users', { baseDir: BaseDirectory.AppLocalData });
```
 ### Remove Call `remove()` to delete a directory. If the directory does not exist, an error is returned. 
```js
import { remove, BaseDirectory } from '@tauri-apps/plugin-fs';
await remove('images', { baseDir: BaseDirectory.AppLocalData });
```
 If the directory is not empty, the `recursive` option must be set to `true`: 
```js
import { remove, BaseDirectory } from '@tauri-apps/plugin-fs';
await remove('images', {
  baseDir: BaseDirectory.AppLocalData,
  recursive: true,
});
```
 ### Exists Use the `exists()` function to check if a directory exists: 
```js
import { exists, BaseDirectory } from '@tauri-apps/plugin-fs';
const tokenExists = await exists('images', {
  baseDir: BaseDirectory.AppLocalData,
});
```
 ### Metadata Directory metadata can be retrieved with the `stat` and the `lstat` functions. `stat` follows symlinks (and returns an error if the actual file it points to is not allowed by the scope) and `lstat` does not follow symlinks, returning the information of the symlink itself. 
```js
import { stat, BaseDirectory } from '@tauri-apps/plugin-fs';
const metadata = await stat('databases', {
  baseDir: BaseDirectory.AppLocalData,
});
```
 ## Watching changes To watch a directory or file for changes, use the `watch` or `watchImmediate` functions. * watch `watch` is debounced so it only emits events after a certain delay: 
  ```js
  import { watch, BaseDirectory } from '@tauri-apps/plugin-fs';
  await watch(
    'app.log',
    (event) => {
      console.log('app.log event', event);
    },
    {
      baseDir: BaseDirectory.AppLog,
      delayMs: 500,
    }
  );
  ```
 * watchImmediate `watchImmediate` immediately notifies listeners of an event: 
  ```js
  import { watchImmediate, BaseDirectory } from '@tauri-apps/plugin-fs';
  await watchImmediate(
    'logs',
    (event) => {
      console.log('logs directory event', event);
    },
    {
      baseDir: BaseDirectory.AppLog,
      recursive: true,
    }
  );
  ```
 By default watch operations on a directory are not recursive. Set the `recursive` option to `true` to recursively watch for changes on all sub-directories. Note The watch functions require the `watch` feature flag: src-tauri/Cargo.toml 
```toml
[dependencies]
tauri-plugin-fs = { version = "2.0.0", features = ["watch"] }
```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. Permissions alone do not grant a scope Enabling a permission such as `fs:allow-exists` by itself does **not** allow access to any path. Most `fs` commands also require a **scope** that explicitly lists which paths the command may access. Without an `allow` scope, calls will fail at runtime with a `forbidden path` error, even though the permission is enabled. Not enough — permission has no scope, so no paths are allowed 
```json
{
  "permissions": ["fs:default", "fs:allow-exists"]
}
```
 Works — the identifier form adds an explicit allow scope 
```json
{
  "permissions": [
    "fs:default",
    {
      "identifier": "fs:allow-exists",
      "allow": [{ "path": "$HOME" }, { "path": "$HOME/**/*" }]
    }
  ]
}
```
 See [Scopes](#scopes) below for the full list of path variables you can use in `allow` and `deny`. src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    +"fs:default",
+    {
      +"identifier": "fs:allow-exists",
      +"allow": [{ "path": "$APPDATA/*" }]
+    }
  ]
}
```
 ## [Default Permission](#default-permission) This set of permissions describes the what kind of file system access the `fs` plugin has enabled or denied by default. #### [Granted Permissions](#granted-permissions) This default permission set enables read access to the application specific directories (AppConfig, AppData, AppLocalData, AppCache, AppLog) and all files and sub directories created in it. The location of these directories depends on the operating system, where the application is run. In general these directories need to be manually created by the application at runtime, before accessing files or folders in it is possible. Therefore, it is also allowed to create all of these folders via the `mkdir` command. #### Denied Permissions This default permission set prevents access to critical components of the Tauri application by default. * On Windows the access to webview data folder `$APPLOCALDATA/EBWebView` is denied. * On Linux the access to webview data paths inside `$APPLOCALDATA` are denied. #### This default permission set includes the following: * `create-app-specific-dirs` * `read-app-specific-dirs-recursive` * `deny-default` ## Permission Table | Identifier | Description | | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | | `fs:allow-app-read-recursive` | This allows full recursive read access to the complete application folders, files and subdirectories. | | `fs:allow-app-write-recursive` | This allows full recursive write access to the complete application folders, files and subdirectories. | | `fs:allow-app-read` | This allows non-recursive read access to the application folders. | | `fs:allow-app-write` | This allows non-recursive write access to the application folders. | | `fs:allow-app-meta-recursive` | This allows full recursive read access to metadata of the application folders, including file listing and statistics. | | `fs:allow-app-meta` | This allows non-recursive read access to metadata of the application folders, including file listing and statistics. | | `fs:scope-app-recursive` | This scope permits recursive access to the complete application folders, including sub directories and files. | | `fs:scope-app` | This scope permits access to all files and list content of top level directories in the application folders. | | `fs:scope-app-index` | This scope permits to list all files and folders in the application directories. | | `fs:allow-appcache-read-recursive` | This allows full recursive read access to the complete `$APPCACHE` folder, files and subdirectories. | | `fs:allow-appcache-write-recursive` | This allows full recursive write access to the complete `$APPCACHE` folder, files and subdirectories. | | `fs:allow-appcache-read` | This allows non-recursive read access to the `$APPCACHE` folder. | | `fs:allow-appcache-write` | This allows non-recursive write access to the `$APPCACHE` folder. | | `fs:allow-appcache-meta-recursive` | This allows full recursive read access to metadata of the `$APPCACHE` folder, including file listing and statistics. | | `fs:allow-appcache-meta` | This allows non-recursive read access to metadata of the `$APPCACHE` folder, including file listing and statistics. | | `fs:scope-appcache-recursive` | This scope permits recursive access to the complete `$APPCACHE` folder, including sub directories and files. | | `fs:scope-appcache` | This scope permits access to all files and list content of top level directories in the `$APPCACHE` folder. | | `fs:scope-appcache-index` | This scope permits to list all files and folders in the `$APPCACHE`folder. | | `fs:allow-appconfig-read-recursive` | This allows full recursive read access to the complete `$APPCONFIG` folder, files and subdirectories. | | `fs:allow-appconfig-write-recursive` | This allows full recursive write access to the complete `$APPCONFIG` folder, files and subdirectories. | | `fs:allow-appconfig-read` | This allows non-recursive read access to the `$APPCONFIG` folder. | | `fs:allow-appconfig-write` | This allows non-recursive write access to the `$APPCONFIG` folder. | | `fs:allow-appconfig-meta-recursive` | This allows full recursive read access to metadata of the `$APPCONFIG` folder, including file listing and statistics. | | `fs:allow-appconfig-meta` | This allows non-recursive read access to metadata of the `$APPCONFIG` folder, including file listing and statistics. | | `fs:scope-appconfig-recursive` | This scope permits recursive access to the complete `$APPCONFIG` folder, including sub directories and files. | | `fs:scope-appconfig` | This scope permits access to all files and list content of top level directories in the `$APPCONFIG` folder. | | `fs:scope-appconfig-index` | This scope permits to list all files and folders in the `$APPCONFIG`folder. | | `fs:allow-appdata-read-recursive` | This allows full recursive read access to the complete `$APPDATA` folder, files and subdirectories. | | `fs:allow-appdata-write-recursive` | This allows full recursive write access to the complete `$APPDATA` folder, files and subdirectories. | | `fs:allow-appdata-read` | This allows non-recursive read access to the `$APPDATA` folder. | | `fs:allow-appdata-write` | This allows non-recursive write access to the `$APPDATA` folder. | | `fs:allow-appdata-meta-recursive` | This allows full recursive read access to metadata of the `$APPDATA` folder, including file listing and statistics. | | `fs:allow-appdata-meta` | This allows non-recursive read access to metadata of the `$APPDATA` folder, including file listing and statistics. | | `fs:scope-appdata-recursive` | This scope permits recursive access to the complete `$APPDATA` folder, including sub directories and files. | | `fs:scope-appdata` | This scope permits access to all files and list content of top level directories in the `$APPDATA` folder. | | `fs:scope-appdata-index` | This scope permits to list all files and folders in the `$APPDATA`folder. | | `fs:allow-applocaldata-read-recursive` | This allows full recursive read access to the complete `$APPLOCALDATA` folder, files and subdirectories. | | `fs:allow-applocaldata-write-recursive` | This allows full recursive write access to the complete `$APPLOCALDATA` folder, files and subdirectories. | | `fs:allow-applocaldata-read` | This allows non-recursive read access to the `$APPLOCALDATA` folder. | | `fs:allow-applocaldata-write` | This allows non-recursive write access to the `$APPLOCALDATA` folder. | | `fs:allow-applocaldata-meta-recursive` | This allows full recursive read access to metadata of the `$APPLOCALDATA` folder, including file listing and statistics. | | `fs:allow-applocaldata-meta` | This allows non-recursive read access to metadata of the `$APPLOCALDATA` folder, including file listing and statistics. | | `fs:scope-applocaldata-recursive` | This scope permits recursive access to the complete `$APPLOCALDATA` folder, including sub directories and files. | | `fs:scope-applocaldata` | This scope permits access to all files and list content of top level directories in the `$APPLOCALDATA` folder. | | `fs:scope-applocaldata-index` | This scope permits to list all files and folders in the `$APPLOCALDATA`folder. | | `fs:allow-applog-read-recursive` | This allows full recursive read access to the complete `$APPLOG` folder, files and subdirectories. | | `fs:allow-applog-write-recursive` | This allows full recursive write access to the complete `$APPLOG` folder, files and subdirectories. | | `fs:allow-applog-read` | This allows non-recursive read access to the `$APPLOG` folder. | | `fs:allow-applog-write` | This allows non-recursive write access to the `$APPLOG` folder. | | `fs:allow-applog-meta-recursive` | This allows full recursive read access to metadata of the `$APPLOG` folder, including file listing and statistics. | | `fs:allow-applog-meta` | This allows non-recursive read access to metadata of the `$APPLOG` folder, including file listing and statistics. | | `fs:scope-applog-recursive` | This scope permits recursive access to the complete `$APPLOG` folder, including sub directories and files. | | `fs:scope-applog` | This scope permits access to all files and list content of top level directories in the `$APPLOG` folder. | | `fs:scope-applog-index` | This scope permits to list all files and folders in the `$APPLOG`folder. | | `fs:allow-audio-read-recursive` | This allows full recursive read access to the complete `$AUDIO` folder, files and subdirectories. | | `fs:allow-audio-write-recursive` | This allows full recursive write access to the complete `$AUDIO` folder, files and subdirectories. | | `fs:allow-audio-read` | This allows non-recursive read access to the `$AUDIO` folder. | | `fs:allow-audio-write` | This allows non-recursive write access to the `$AUDIO` folder. | | `fs:allow-audio-meta-recursive` | This allows full recursive read access to metadata of the `$AUDIO` folder, including file listing and statistics. | | `fs:allow-audio-meta` | This allows non-recursive read access to metadata of the `$AUDIO` folder, including file listing and statistics. | | `fs:scope-audio-recursive` | This scope permits recursive access to the complete `$AUDIO` folder, including sub directories and files. | | `fs:scope-audio` | This scope permits access to all files and list content of top level directories in the `$AUDIO` folder. | | `fs:scope-audio-index` | This scope permits to list all files and folders in the `$AUDIO`folder. | | `fs:allow-cache-read-recursive` | This allows full recursive read access to the complete `$CACHE` folder, files and subdirectories. | | `fs:allow-cache-write-recursive` | This allows full recursive write access to the complete `$CACHE` folder, files and subdirectories. | | `fs:allow-cache-read` | This allows non-recursive read access to the `$CACHE` folder. | | `fs:allow-cache-write` | This allows non-recursive write access to the `$CACHE` folder. | | `fs:allow-cache-meta-recursive` | This allows full recursive read access to metadata of the `$CACHE` folder, including file listing and statistics. | | `fs:allow-cache-meta` | This allows non-recursive read access to metadata of the `$CACHE` folder, including file listing and statistics. | | `fs:scope-cache-recursive` | This scope permits recursive access to the complete `$CACHE` folder, including sub directories and files. | | `fs:scope-cache` | This scope permits access to all files and list content of top level directories in the `$CACHE` folder. | | `fs:scope-cache-index` | This scope permits to list all files and folders in the `$CACHE`folder. | | `fs:allow-config-read-recursive` | This allows full recursive read access to the complete `$CONFIG` folder, files and subdirectories. | | `fs:allow-config-write-recursive` | This allows full recursive write access to the complete `$CONFIG` folder, files and subdirectories. | | `fs:allow-config-read` | This allows non-recursive read access to the `$CONFIG` folder. | | `fs:allow-config-write` | This allows non-recursive write access to the `$CONFIG` folder. | | `fs:allow-config-meta-recursive` | This allows full recursive read access to metadata of the `$CONFIG` folder, including file listing and statistics. | | `fs:allow-config-meta` | This allows non-recursive read access to metadata of the `$CONFIG` folder, including file listing and statistics. | | `fs:scope-config-recursive` | This scope permits recursive access to the complete `$CONFIG` folder, including sub directories and files. | | `fs:scope-config` | This scope permits access to all files and list content of top level directories in the `$CONFIG` folder. | | `fs:scope-config-index` | This scope permits to list all files and folders in the `$CONFIG`folder. | | `fs:allow-data-read-recursive` | This allows full recursive read access to the complete `$DATA` folder, files and subdirectories. | | `fs:allow-data-write-recursive` | This allows full recursive write access to the complete `$DATA` folder, files and subdirectories. | | `fs:allow-data-read` | This allows non-recursive read access to the `$DATA` folder. | | `fs:allow-data-write` | This allows non-recursive write access to the `$DATA` folder. | | `fs:allow-data-meta-recursive` | This allows full recursive read access to metadata of the `$DATA` folder, including file listing and statistics. | | `fs:allow-data-meta` | This allows non-recursive read access to metadata of the `$DATA` folder, including file listing and statistics. | | `fs:scope-data-recursive` | This scope permits recursive access to the complete `$DATA` folder, including sub directories and files. | | `fs:scope-data` | This scope permits access to all files and list content of top level directories in the `$DATA` folder. | | `fs:scope-data-index` | This scope permits to list all files and folders in the `$DATA`folder. | | `fs:allow-desktop-read-recursive` | This allows full recursive read access to the complete `$DESKTOP` folder, files and subdirectories. | | `fs:allow-desktop-write-recursive` | This allows full recursive write access to the complete `$DESKTOP` folder, files and subdirectories. | | `fs:allow-desktop-read` | This allows non-recursive read access to the `$DESKTOP` folder. | | `fs:allow-desktop-write` | This allows non-recursive write access to the `$DESKTOP` folder. | | `fs:allow-desktop-meta-recursive` | This allows full recursive read access to metadata of the `$DESKTOP` folder, including file listing and statistics. | | `fs:allow-desktop-meta` | This allows non-recursive read access to metadata of the `$DESKTOP` folder, including file listing and statistics. | | `fs:scope-desktop-recursive` | This scope permits recursive access to the complete `$DESKTOP` folder, including sub directories and files. | | `fs:scope-desktop` | This scope permits access to all files and list content of top level directories in the `$DESKTOP` folder. | | `fs:scope-desktop-index` | This scope permits to list all files and folders in the `$DESKTOP`folder. | | `fs:allow-document-read-recursive` | This allows full recursive read access to the complete `$DOCUMENT` folder, files and subdirectories. | | `fs:allow-document-write-recursive` | This allows full recursive write access to the complete `$DOCUMENT` folder, files and subdirectories. | | `fs:allow-document-read` | This allows non-recursive read access to the `$DOCUMENT` folder. | | `fs:allow-document-write` | This allows non-recursive write access to the `$DOCUMENT` folder. | | `fs:allow-document-meta-recursive` | This allows full recursive read access to metadata of the `$DOCUMENT` folder, including file listing and statistics. | | `fs:allow-document-meta` | This allows non-recursive read access to metadata of the `$DOCUMENT` folder, including file listing and statistics. | | `fs:scope-document-recursive` | This scope permits recursive access to the complete `$DOCUMENT` folder, including sub directories and files. | | `fs:scope-document` | This scope permits access to all files and list content of top level directories in the `$DOCUMENT` folder. | | `fs:scope-document-index` | This scope permits to list all files and folders in the `$DOCUMENT`folder. | | `fs:allow-download-read-recursive` | This allows full recursive read access to the complete `$DOWNLOAD` folder, files and subdirectories. | | `fs:allow-download-write-recursive` | This allows full recursive write access to the complete `$DOWNLOAD` folder, files and subdirectories. | | `fs:allow-download-read` | This allows non-recursive read access to the `$DOWNLOAD` folder. | | `fs:allow-download-write` | This allows non-recursive write access to the `$DOWNLOAD` folder. | | `fs:allow-download-meta-recursive` | This allows full recursive read access to metadata of the `$DOWNLOAD` folder, including file listing and statistics. | | `fs:allow-download-meta` | This allows non-recursive read access to metadata of the `$DOWNLOAD` folder, including file listing and statistics. | | `fs:scope-download-recursive` | This scope permits recursive access to the complete `$DOWNLOAD` folder, including sub directories and files. | | `fs:scope-download` | This scope permits access to all files and list content of top level directories in the `$DOWNLOAD` folder. | | `fs:scope-download-index` | This scope permits to list all files and folders in the `$DOWNLOAD`folder. | | `fs:allow-exe-read-recursive` | This allows full recursive read access to the complete `$EXE` folder, files and subdirectories. | | `fs:allow-exe-write-recursive` | This allows full recursive write access to the complete `$EXE` folder, files and subdirectories. | | `fs:allow-exe-read` | This allows non-recursive read access to the `$EXE` folder. | | `fs:allow-exe-write` | This allows non-recursive write access to the `$EXE` folder. | | `fs:allow-exe-meta-recursive` | This allows full recursive read access to metadata of the `$EXE` folder, including file listing and statistics. | | `fs:allow-exe-meta` | This allows non-recursive read access to metadata of the `$EXE` folder, including file listing and statistics. | | `fs:scope-exe-recursive` | This scope permits recursive access to the complete `$EXE` folder, including sub directories and files. | | `fs:scope-exe` | This scope permits access to all files and list content of top level directories in the `$EXE` folder. | | `fs:scope-exe-index` | This scope permits to list all files and folders in the `$EXE`folder. | | `fs:allow-font-read-recursive` | This allows full recursive read access to the complete `$FONT` folder, files and subdirectories. | | `fs:allow-font-write-recursive` | This allows full recursive write access to the complete `$FONT` folder, files and subdirectories. | | `fs:allow-font-read` | This allows non-recursive read access to the `$FONT` folder. | | `fs:allow-font-write` | This allows non-recursive write access to the `$FONT` folder. | | `fs:allow-font-meta-recursive` | This allows full recursive read access to metadata of the `$FONT` folder, including file listing and statistics. | | `fs:allow-font-meta` | This allows non-recursive read access to metadata of the `$FONT` folder, including file listing and statistics. | | `fs:scope-font-recursive` | This scope permits recursive access to the complete `$FONT` folder, including sub directories and files. | | `fs:scope-font` | This scope permits access to all files and list content of top level directories in the `$FONT` folder. | | `fs:scope-font-index` | This scope permits to list all files and folders in the `$FONT`folder. | | `fs:allow-home-read-recursive` | This allows full recursive read access to the complete `$HOME` folder, files and subdirectories. | | `fs:allow-home-write-recursive` | This allows full recursive write access to the complete `$HOME` folder, files and subdirectories. | | `fs:allow-home-read` | This allows non-recursive read access to the `$HOME` folder. | | `fs:allow-home-write` | This allows non-recursive write access to the `$HOME` folder. | | `fs:allow-home-meta-recursive` | This allows full recursive read access to metadata of the `$HOME` folder, including file listing and statistics. | | `fs:allow-home-meta` | This allows non-recursive read access to metadata of the `$HOME` folder, including file listing and statistics. | | `fs:scope-home-recursive` | This scope permits recursive access to the complete `$HOME` folder, including sub directories and files. | | `fs:scope-home` | This scope permits access to all files and list content of top level directories in the `$HOME` folder. | | `fs:scope-home-index` | This scope permits to list all files and folders in the `$HOME`folder. | | `fs:allow-localdata-read-recursive` | This allows full recursive read access to the complete `$LOCALDATA` folder, files and subdirectories. | | `fs:allow-localdata-write-recursive` | This allows full recursive write access to the complete `$LOCALDATA` folder, files and subdirectories. | | `fs:allow-localdata-read` | This allows non-recursive read access to the `$LOCALDATA` folder. | | `fs:allow-localdata-write` | This allows non-recursive write access to the `$LOCALDATA` folder. | | `fs:allow-localdata-meta-recursive` | This allows full recursive read access to metadata of the `$LOCALDATA` folder, including file listing and statistics. | | `fs:allow-localdata-meta` | This allows non-recursive read access to metadata of the `$LOCALDATA` folder, including file listing and statistics. | | `fs:scope-localdata-recursive` | This scope permits recursive access to the complete `$LOCALDATA` folder, including sub directories and files. | | `fs:scope-localdata` | This scope permits access to all files and list content of top level directories in the `$LOCALDATA` folder. | | `fs:scope-localdata-index` | This scope permits to list all files and folders in the `$LOCALDATA`folder. | | `fs:allow-log-read-recursive` | This allows full recursive read access to the complete `$LOG` folder, files and subdirectories. | | `fs:allow-log-write-recursive` | This allows full recursive write access to the complete `$LOG` folder, files and subdirectories. | | `fs:allow-log-read` | This allows non-recursive read access to the `$LOG` folder. | | `fs:allow-log-write` | This allows non-recursive write access to the `$LOG` folder. | | `fs:allow-log-meta-recursive` | This allows full recursive read access to metadata of the `$LOG` folder, including file listing and statistics. | | `fs:allow-log-meta` | This allows non-recursive read access to metadata of the `$LOG` folder, including file listing and statistics. | | `fs:scope-log-recursive` | This scope permits recursive access to the complete `$LOG` folder, including sub directories and files. | | `fs:scope-log` | This scope permits access to all files and list content of top level directories in the `$LOG` folder. | | `fs:scope-log-index` | This scope permits to list all files and folders in the `$LOG`folder. | | `fs:allow-picture-read-recursive` | This allows full recursive read access to the complete `$PICTURE` folder, files and subdirectories. | | `fs:allow-picture-write-recursive` | This allows full recursive write access to the complete `$PICTURE` folder, files and subdirectories. | | `fs:allow-picture-read` | This allows non-recursive read access to the `$PICTURE` folder. | | `fs:allow-picture-write` | This allows non-recursive write access to the `$PICTURE` folder. | | `fs:allow-picture-meta-recursive` | This allows full recursive read access to metadata of the `$PICTURE` folder, including file listing and statistics. | | `fs:allow-picture-meta` | This allows non-recursive read access to metadata of the `$PICTURE` folder, including file listing and statistics. | | `fs:scope-picture-recursive` | This scope permits recursive access to the complete `$PICTURE` folder, including sub directories and files. | | `fs:scope-picture` | This scope permits access to all files and list content of top level directories in the `$PICTURE` folder. | | `fs:scope-picture-index` | This scope permits to list all files and folders in the `$PICTURE`folder. | | `fs:allow-public-read-recursive` | This allows full recursive read access to the complete `$PUBLIC` folder, files and subdirectories. | | `fs:allow-public-write-recursive` | This allows full recursive write access to the complete `$PUBLIC` folder, files and subdirectories. | | `fs:allow-public-read` | This allows non-recursive read access to the `$PUBLIC` folder. | | `fs:allow-public-write` | This allows non-recursive write access to the `$PUBLIC` folder. | | `fs:allow-public-meta-recursive` | This allows full recursive read access to metadata of the `$PUBLIC` folder, including file listing and statistics. | | `fs:allow-public-meta` | This allows non-recursive read access to metadata of the `$PUBLIC` folder, including file listing and statistics. | | `fs:scope-public-recursive` | This scope permits recursive access to the complete `$PUBLIC` folder, including sub directories and files. | | `fs:scope-public` | This scope permits access to all files and list content of top level directories in the `$PUBLIC` folder. | | `fs:scope-public-index` | This scope permits to list all files and folders in the `$PUBLIC`folder. | | `fs:allow-resource-read-recursive` | This allows full recursive read access to the complete `$RESOURCE` folder, files and subdirectories. | | `fs:allow-resource-write-recursive` | This allows full recursive write access to the complete `$RESOURCE` folder, files and subdirectories. | | `fs:allow-resource-read` | This allows non-recursive read access to the `$RESOURCE` folder. | | `fs:allow-resource-write` | This allows non-recursive write access to the `$RESOURCE` folder. | | `fs:allow-resource-meta-recursive` | This allows full recursive read access to metadata of the `$RESOURCE` folder, including file listing and statistics. | | `fs:allow-resource-meta` | This allows non-recursive read access to metadata of the `$RESOURCE` folder, including file listing and statistics. | | `fs:scope-resource-recursive` | This scope permits recursive access to the complete `$RESOURCE` folder, including sub directories and files. | | `fs:scope-resource` | This scope permits access to all files and list content of top level directories in the `$RESOURCE` folder. | | `fs:scope-resource-index` | This scope permits to list all files and folders in the `$RESOURCE`folder. | | `fs:allow-runtime-read-recursive` | This allows full recursive read access to the complete `$RUNTIME` folder, files and subdirectories. | | `fs:allow-runtime-write-recursive` | This allows full recursive write access to the complete `$RUNTIME` folder, files and subdirectories. | | `fs:allow-runtime-read` | This allows non-recursive read access to the `$RUNTIME` folder. | | `fs:allow-runtime-write` | This allows non-recursive write access to the `$RUNTIME` folder. | | `fs:allow-runtime-meta-recursive` | This allows full recursive read access to metadata of the `$RUNTIME` folder, including file listing and statistics. | | `fs:allow-runtime-meta` | This allows non-recursive read access to metadata of the `$RUNTIME` folder, including file listing and statistics. | | `fs:scope-runtime-recursive` | This scope permits recursive access to the complete `$RUNTIME` folder, including sub directories and files. | | `fs:scope-runtime` | This scope permits access to all files and list content of top level directories in the `$RUNTIME` folder. | | `fs:scope-runtime-index` | This scope permits to list all files and folders in the `$RUNTIME`folder. | | `fs:allow-temp-read-recursive` | This allows full recursive read access to the complete `$TEMP` folder, files and subdirectories. | | `fs:allow-temp-write-recursive` | This allows full recursive write access to the complete `$TEMP` folder, files and subdirectories. | | `fs:allow-temp-read` | This allows non-recursive read access to the `$TEMP` folder. | | `fs:allow-temp-write` | This allows non-recursive write access to the `$TEMP` folder. | | `fs:allow-temp-meta-recursive` | This allows full recursive read access to metadata of the `$TEMP` folder, including file listing and statistics. | | `fs:allow-temp-meta` | This allows non-recursive read access to metadata of the `$TEMP` folder, including file listing and statistics. | | `fs:scope-temp-recursive` | This scope permits recursive access to the complete `$TEMP` folder, including sub directories and files. | | `fs:scope-temp` | This scope permits access to all files and list content of top level directories in the `$TEMP` folder. | | `fs:scope-temp-index` | This scope permits to list all files and folders in the `$TEMP`folder. | | `fs:allow-template-read-recursive` | This allows full recursive read access to the complete `$TEMPLATE` folder, files and subdirectories. | | `fs:allow-template-write-recursive` | This allows full recursive write access to the complete `$TEMPLATE` folder, files and subdirectories. | | `fs:allow-template-read` | This allows non-recursive read access to the `$TEMPLATE` folder. | | `fs:allow-template-write` | This allows non-recursive write access to the `$TEMPLATE` folder. | | `fs:allow-template-meta-recursive` | This allows full recursive read access to metadata of the `$TEMPLATE` folder, including file listing and statistics. | | `fs:allow-template-meta` | This allows non-recursive read access to metadata of the `$TEMPLATE` folder, including file listing and statistics. | | `fs:scope-template-recursive` | This scope permits recursive access to the complete `$TEMPLATE` folder, including sub directories and files. | | `fs:scope-template` | This scope permits access to all files and list content of top level directories in the `$TEMPLATE` folder. | | `fs:scope-template-index` | This scope permits to list all files and folders in the `$TEMPLATE`folder. | | `fs:allow-video-read-recursive` | This allows full recursive read access to the complete `$VIDEO` folder, files and subdirectories. | | `fs:allow-video-write-recursive` | This allows full recursive write access to the complete `$VIDEO` folder, files and subdirectories. | | `fs:allow-video-read` | This allows non-recursive read access to the `$VIDEO` folder. | | `fs:allow-video-write` | This allows non-recursive write access to the `$VIDEO` folder. | | `fs:allow-video-meta-recursive` | This allows full recursive read access to metadata of the `$VIDEO` folder, including file listing and statistics. | | `fs:allow-video-meta` | This allows non-recursive read access to metadata of the `$VIDEO` folder, including file listing and statistics. | | `fs:scope-video-recursive` | This scope permits recursive access to the complete `$VIDEO` folder, including sub directories and files. | | `fs:scope-video` | This scope permits access to all files and list content of top level directories in the `$VIDEO` folder. | | `fs:scope-video-index` | This scope permits to list all files and folders in the `$VIDEO`folder. | | `fs:allow-copy-file` | Enables the copy_file command without any pre-configured scope. | | `fs:deny-copy-file` | Denies the copy_file command without any pre-configured scope. | | `fs:allow-create` | Enables the create command without any pre-configured scope. | | `fs:deny-create` | Denies the create command without any pre-configured scope. | | `fs:allow-exists` | Enables the exists command without any pre-configured scope. | | `fs:deny-exists` | Denies the exists command without any pre-configured scope. | | `fs:allow-fstat` | Enables the fstat command without any pre-configured scope. | | `fs:deny-fstat` | Denies the fstat command without any pre-configured scope. | | `fs:allow-ftruncate` | Enables the ftruncate command without any pre-configured scope. | | `fs:deny-ftruncate` | Denies the ftruncate command without any pre-configured scope. | | `fs:allow-lstat` | Enables the lstat command without any pre-configured scope. | | `fs:deny-lstat` | Denies the lstat command without any pre-configured scope. | | `fs:allow-mkdir` | Enables the mkdir command without any pre-configured scope. | | `fs:deny-mkdir` | Denies the mkdir command without any pre-configured scope. | | `fs:allow-open` | Enables the open command without any pre-configured scope. | | `fs:deny-open` | Denies the open command without any pre-configured scope. | | `fs:allow-read` | Enables the read command without any pre-configured scope. | | `fs:deny-read` | Denies the read command without any pre-configured scope. | | `fs:allow-read-dir` | Enables the read_dir command without any pre-configured scope. | | `fs:deny-read-dir` | Denies the read_dir command without any pre-configured scope. | | `fs:allow-read-file` | Enables the read_file command without any pre-configured scope. | | `fs:deny-read-file` | Denies the read_file command without any pre-configured scope. | | `fs:allow-read-text-file` | Enables the read_text_file command without any pre-configured scope. | | `fs:deny-read-text-file` | Denies the read_text_file command without any pre-configured scope. | | `fs:allow-read-text-file-lines` | Enables the read_text_file_lines command without any pre-configured scope. | | `fs:deny-read-text-file-lines` | Denies the read_text_file_lines command without any pre-configured scope. | | `fs:allow-read-text-file-lines-next` | Enables the read_text_file_lines_next command without any pre-configured scope. | | `fs:deny-read-text-file-lines-next` | Denies the read_text_file_lines_next command without any pre-configured scope. | | `fs:allow-remove` | Enables the remove command without any pre-configured scope. | | `fs:deny-remove` | Denies the remove command without any pre-configured scope. | | `fs:allow-rename` | Enables the rename command without any pre-configured scope. | | `fs:deny-rename` | Denies the rename command without any pre-configured scope. | | `fs:allow-seek` | Enables the seek command without any pre-configured scope. | | `fs:deny-seek` | Denies the seek command without any pre-configured scope. | | `fs:allow-size` | Enables the size command without any pre-configured scope. | | `fs:deny-size` | Denies the size command without any pre-configured scope. | | `fs:allow-start-accessing-security-scoped-resource` | Enables the start_accessing_security_scoped_resource command without any pre-configured scope. | | `fs:deny-start-accessing-security-scoped-resource` | Denies the start_accessing_security_scoped_resource command without any pre-configured scope. | | `fs:allow-stat` | Enables the stat command without any pre-configured scope. | | `fs:deny-stat` | Denies the stat command without any pre-configured scope. | | `fs:allow-stop-accessing-security-scoped-resource` | Enables the stop_accessing_security_scoped_resource command without any pre-configured scope. | | `fs:deny-stop-accessing-security-scoped-resource` | Denies the stop_accessing_security_scoped_resource command without any pre-configured scope. | | `fs:allow-truncate` | Enables the truncate command without any pre-configured scope. | | `fs:deny-truncate` | Denies the truncate command without any pre-configured scope. | | `fs:allow-unwatch` | Enables the unwatch command without any pre-configured scope. | | `fs:deny-unwatch` | Denies the unwatch command without any pre-configured scope. | | `fs:allow-watch` | Enables the watch command without any pre-configured scope. | | `fs:deny-watch` | Denies the watch command without any pre-configured scope. | | `fs:allow-write` | Enables the write command without any pre-configured scope. | | `fs:deny-write` | Denies the write command without any pre-configured scope. | | `fs:allow-write-file` | Enables the write_file command without any pre-configured scope. | | `fs:deny-write-file` | Denies the write_file command without any pre-configured scope. | | `fs:allow-write-text-file` | Enables the write_text_file command without any pre-configured scope. | | `fs:deny-write-text-file` | Denies the write_text_file command without any pre-configured scope. | | `fs:create-app-specific-dirs` | This permissions allows to create the application specific directories. | | `fs:deny-default` | This denies access to dangerous Tauri relevant files and folders by default. | | `fs:deny-webview-data-linux` | This denies access to the following paths- `$APPLOCALDATA/CacheStorage/**` - `$APPLOCALDATA/cookies` - `$APPLOCALDATA/hsts-storage.sqlite` - `$APPLOCALDATA/serviceworkers/**` - `$APPLOCALDATA/WebKitCache/**` - `$APPLOCALDATA/databases/**` - `$APPLOCALDATA/localstorage/**` - `$APPLOCALDATA/mediakeys/**` - `$APPLOCALDATA/storage/**`on linux as the webview data and configuration values are stored here. Allowing access can lead to sensitive information disclosure and should be well considered. | | `fs:deny-webview-data-windows` | This denies access to the `$APPLOCALDATA/EBWebView` folder on windows as the webview data and configuration values are stored here. Allowing access can lead to sensitive information disclosure and should be well considered. | | `fs:read-all` | This enables all read related commands without any pre-configured accessible paths. | | `fs:read-app-specific-dirs-recursive` | This permission allows recursive read functionality on the application specific base directories. | | `fs:read-dirs` | This enables directory read and file metadata related commands without any pre-configured accessible paths. | | `fs:read-files` | This enables file read related commands without any pre-configured accessible paths. | | `fs:read-meta` | This enables all index or metadata related commands without any pre-configured accessible paths. | | `fs:scope` | An empty permission you can use to modify the global scope.## Example``` { "identifier": "read-documents", "windows": ["main"], "permissions": [ "fs:allow-read", { "identifier": "fs:scope", "allow": [ "$APPDATA/documents/**/*" ], "deny": [ "$APPDATA/documents/secret.txt" ] } ] } 
```                                                                                                                                                  |
| `fs:write-all`                                      | This enables all write related commands without any pre-configured accessible paths.                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `fs:write-files`                                    | This enables all file write related commands without any pre-configured accessible paths.                                                                                                                                                                                                                                                                                                                                                                                                                      |

### Scopes

This plugin permissions includes scopes for defining which paths are allowed or explicitly rejected. For more information on scopes, see the [Command Scopes](/security/scope/).

Each `allow` or `deny` scope must include an array listing all paths that should be allowed or denied. The scope entries are in the `{ path: string }` format.

Note

`deny` take precedence over `allow` so if a path is denied by a scope, it will be blocked at runtime even if it is allowed by another scope.

Scope entries can use `$<path>` variables to reference common system paths such as the home directory, the app resources directory and the config directory. The following table lists all common paths you can reference:

| Path                                                                        | Variable      |
| --------------------------------------------------------------------------- | ------------- |
| [appConfigDir](/reference/javascript/api/namespacepath/#appconfigdir)       | $APPCONFIG    |
| [appDataDir](/reference/javascript/api/namespacepath/#appdatadir)           | $APPDATA      |
| [appLocalDataDir](/reference/javascript/api/namespacepath/#applocaldatadir) | $APPLOCALDATA |
| [appcacheDir](/reference/javascript/api/namespacepath/#appcachedir)         | $APPCACHE     |
| [applogDir](/reference/javascript/api/namespacepath/#applogdir)             | $APPLOG       |
| [audioDir](/reference/javascript/api/namespacepath/#audiodir)               | $AUDIO        |
| [cacheDir](/reference/javascript/api/namespacepath/#cachedir)               | $CACHE        |
| [configDir](/reference/javascript/api/namespacepath/#configdir)             | $CONFIG       |
| [dataDir](/reference/javascript/api/namespacepath/#datadir)                 | $DATA         |
| [localDataDir](/reference/javascript/api/namespacepath/#localdatadir)       | $LOCALDATA    |
| [desktopDir](/reference/javascript/api/namespacepath/#desktopdir)           | $DESKTOP      |
| [documentDir](/reference/javascript/api/namespacepath/#documentdir)         | $DOCUMENT     |
| [downloadDir](/reference/javascript/api/namespacepath/#downloaddir)         | $DOWNLOAD     |
| [executableDir](/reference/javascript/api/namespacepath/#executabledir)     | $EXE          |
| [fontDir](/reference/javascript/api/namespacepath/#fontdir)                 | $FONT         |
| [homeDir](/reference/javascript/api/namespacepath/#homedir)                 | $HOME         |
| [pictureDir](/reference/javascript/api/namespacepath/#picturedir)           | $PICTURE      |
| [publicDir](/reference/javascript/api/namespacepath/#publicdir)             | $PUBLIC       |
| [runtimeDir](/reference/javascript/api/namespacepath/#runtimedir)           | $RUNTIME      |
| [templateDir](/reference/javascript/api/namespacepath/#templatedir)         | $TEMPLATE     |
| [videoDir](/reference/javascript/api/namespacepath/#videodir)               | $VIDEO        |
| [resourceDir](/reference/javascript/api/namespacepath/#resourcedir)         | $RESOURCE     |
| [tempDir](/reference/javascript/api/namespacepath/#tempdir)                 | $TEMP         |

#### Examples

* global scope

To apply a scope to any `fs` command, use the `fs:scope` permission:

src-tauri/capabilities/default.json

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    {
      "identifier": "fs:scope",
      "allow": [{ "path": "$APPDATA" }, { "path": "$APPDATA/**/*" }]
    }
  ]
}
```
 To apply a scope to a specific `fs` command, use the object form of permissions `{ "identifier": string, "allow"?: [], "deny"?: [] }`: src-tauri/capabilities/default.json 
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    {
      "identifier": "fs:allow-rename",
      "allow": [{ "path": "$HOME/**/*" }]
    },
    {
      "identifier": "fs:allow-rename",
      "deny": [{ "path": "$HOME/.config/**/*" }]
    },
    {
      "identifier": "fs:allow-exists",
      "allow": [{ "path": "$APPDATA/*" }]
    }
  ]
}
```
 In the above example you can use the [`exists`](#exists) API using any `$APPDATA` sub path (does not include sub-directories) and the [`rename`](#rename)

# Geolocation

> Get and track the device's current position, including information about altitude, heading, and speed (if available).

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/geolocation)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-geolocation)[crates.io](https://crates.io/crates/tauri-plugin-geolocation) API Reference:[](/reference/javascript/geolocation/)[](https://docs.rs/tauri-plugin-geolocation) Get and track the device’s current position, including information about altitude, heading, and speed (if available). ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the geolocation plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add geolocation
    ```
 * yarn 
    ```sh
    yarn run tauri add geolocation
    ```
 * pnpm 
    ```sh
    pnpm tauri add geolocation
    ```
 * deno 
    ```sh
    deno task tauri add geolocation
    ```
 * bun 
    ```sh
    bun tauri add geolocation
    ```
 * cargo 
    ```sh
    cargo tauri add geolocation
    ```
 * Manual 
  ```sh
  npm run tauri add geolocation
  ```
 * npm 
  ```sh
  yarn run tauri add geolocation
  ```
 * yarn 
  ```sh
  pnpm tauri add geolocation
  ```
 * pnpm 
  ```sh
  deno task tauri add geolocation
  ```
 * deno 
  ```sh
  bun tauri add geolocation
  ```
 * bun 
  ```sh
  cargo tauri add geolocation
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-geolocation --target 'cfg(any(target_os = "android", target_os = "ios"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(mobile)]
                 +app.handle().plugin(tauri_plugin_geolocation::init());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-geolocation
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-geolocation
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-geolocation
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-geolocation
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-geolocation
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-geolocation
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-geolocation
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-geolocation
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-geolocation
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-geolocation
  ```
 ## Configuration ### iOS Apple requires privacy descriptions to be specified in Info.plist for location information, where you should describe why your app needs to access it. Illustrated below is an example description: 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>NSLocationWhenInUseUsageDescription</key>
        <string>Required to do XY</string>
    </dict>
</plist>
```
 ### Android This plugin automatically adds the following permissions to your `AndroidManifest.xml` file: 
```xml
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```
 If your app requires GPS functionality to function, you should add the following to your `AndroidManifest.xml` file: 
```xml
<uses-feature android:name="android.hardware.location.gps" android:required="true" />
```
 The Google Play Store uses this property to decide whether it should show the app to devices without GPS capabilities. ## Usage The geolocation plugin is available in JavaScript. 
```javascript
import {
  checkPermissions,
  requestPermissions,
  getCurrentPosition,
  watchPosition,
} from '@tauri-apps/plugin-geolocation';


let permissions = await checkPermissions();
if (
  permissions.location === 'prompt' ||
  permissions.location === 'prompt-with-rationale'
) {
  permissions = await requestPermissions(['location']);
}


if (permissions.location === 'granted') {
  const pos = await getCurrentPosition();


  await watchPosition(
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
    (pos) => {
      console.log(pos);
    }
  );
}
```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/mobile.json 
```diff
{
  "$schema": "../gen/schemas/mobile-schema.json",
  "identifier": "mobile-capability",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": [
    +"core:default",
    +"geolocation:allow-check-permissions",
    +"geolocation:allow-request-permissions",
    +"geolocation:allow-get-current-position",
    +"geolocation:allow-watch-position"
  ]
}
```
 ## [Permission Table](#permission-table) | Identifier | Description | | ---------------------------------------- | -------------------------------------------------------------------------- | | `geolocation:allow-check-permissions` | Enables the check_permissions command without any pre-configured scope. | | `geolocation:deny-check-permissions` | Denies the check_permissions command without any pre-configured scope. | | `geolocation:allow-clear-permissions` | Enables the clear_permissions command without any pre-configured scope. | | `geolocation:deny-clear-permissions` | Denies the clear_permissions command without any pre-configured scope. | | `geolocation:allow-clear-watch` | Enables the clear_watch command without any pre-configured scope. | | `geolocation:deny-clear-watch` | Denies the clear_watch command without any pre-configured scope. | | `geolocation:allow-get-current-position` | Enables the get_current_position command without any pre-configured scope. | | `geolocation:deny-get-current-position` | Denies the get_current_position command without any pre-configured scope. | | `geolocation:allow-request-permissions` | Enables the request_permissions command without any pre-configured scope. | | `geolocation:deny-request-permissions` | Denies the request_permissions command without any pre-configured scope. | | `geolocation:allow-watch-position` | Enables the watch_position command without any pre-configured scope. | | `geolocation:deny-watch-position` | Denies the watch_position command without any pre-configured scope. |

# Global Shortcut

> Register global shortcuts.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/global-shortcut)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-global-shortcut)[crates.io](https://crates.io/crates/tauri-plugin-global-shortcut) API Reference:[](/reference/javascript/global-shortcut/)[](https://docs.rs/tauri-plugin-global-shortcut) Register global shortcuts. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the global-shortcut plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add global-shortcut
    ```
 * yarn 
    ```sh
    yarn run tauri add global-shortcut
    ```
 * pnpm 
    ```sh
    pnpm tauri add global-shortcut
    ```
 * deno 
    ```sh
    deno task tauri add global-shortcut
    ```
 * bun 
    ```sh
    bun tauri add global-shortcut
    ```
 * cargo 
    ```sh
    cargo tauri add global-shortcut
    ```
 * Manual 
  ```sh
  npm run tauri add global-shortcut
  ```
 * npm 
  ```sh
  yarn run tauri add global-shortcut
  ```
 * yarn 
  ```sh
  pnpm tauri add global-shortcut
  ```
 * pnpm 
  ```sh
  deno task tauri add global-shortcut
  ```
 * deno 
  ```sh
  bun tauri add global-shortcut
  ```
 * bun 
  ```sh
  cargo tauri add global-shortcut
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-global-shortcut --target 'cfg(any(target_os = "macos", windows, target_os = "linux"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(desktop)]
                 +app.handle().plugin(tauri_plugin_global_shortcut::Builder::new().build());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-global-shortcut
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-global-shortcut
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-global-shortcut
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-global-shortcut
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-global-shortcut
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-global-shortcut
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-global-shortcut
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-global-shortcut
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-global-shortcut
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-global-shortcut
  ```
 ## Usage The global-shortcut plugin is available in both JavaScript and Rust. * JavaScript 
  ```javascript
  import { register } from '@tauri-apps/plugin-global-shortcut';
  // when using `"withGlobalTauri": true`, you may use
  // const { register } = window.__TAURI__.globalShortcut;


  await register('CommandOrControl+Shift+C', () => {
    console.log('Shortcut triggered');
  });
  ```
 * Rust src-tauri/src/lib.rs 
  ```rust
  pub fn run() {
      tauri::Builder::default()
          .setup(|app| {
              #[cfg(desktop)]
              {
                  use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};


                  let ctrl_n_shortcut = Shortcut::new(Some(Modifiers::CONTROL), Code::KeyN);
                  app.handle().plugin(
                      tauri_plugin_global_shortcut::Builder::new().with_handler(move |_app, shortcut, event| {
                          println!("{:?}", shortcut);
                          if shortcut == &ctrl_n_shortcut {
                              match event.state() {
                                ShortcutState::Pressed => {
                                  println!("Ctrl-N Pressed!");
                                }
                                ShortcutState::Released => {
                                  println!("Ctrl-N Released!");
                                }
                              }
                          }
                      })
                      .build(),
                  )?;


                  app.global_shortcut().register(ctrl_n_shortcut)?;
              }
              Ok(())
          })
          .run(tauri::generate_context!())
          .expect("error while running tauri application");
  }
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    +"global-shortcut:allow-is-registered",
    +"global-shortcut:allow-register",
    +"global-shortcut:allow-unregister"
  ]
}
```
 ## [Default Permission](#default-permission) No features are enabled by default, as we believe the shortcuts can be inherently dangerous and it is application specific if specific shortcuts should be registered or unregistered. ## Permission Table | Identifier | Description | | -------------------------------------- | -------------------------------------------------------------------- | | `global-shortcut:allow-is-registered` | Enables the is_registered command without any pre-configured scope. | | `global-shortcut:deny-is-registered` | Denies the is_registered command without any pre-configured scope. | | `global-shortcut:allow-register` | Enables the register command without any pre-configured scope. | | `global-shortcut:deny-register` | Denies the register command without any pre-configured scope. | | `global-shortcut:allow-register-all` | Enables the register_all command without any pre-configured scope. | | `global-shortcut:deny-register-all` | Denies the register_all command without any pre-configured scope. | | `global-shortcut:allow-unregister` | Enables the unregister command without any pre-configured scope. | | `global-shortcut:deny-unregister` | Denies the unregister command without any pre-configured scope. | | `global-shortcut:allow-unregister-all` | Enables the unregister_all command without any pre-configured scope. | | `global-shortcut:deny-unregister-all` | Denies the unregister_all command without any pre-configured scope. |

# Haptics

> Haptic feedback and vibrations on Android and iOS

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/haptics)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-haptics)[crates.io](https://crates.io/crates/tauri-plugin-haptics) API Reference:[](/reference/javascript/haptics/)[](https://docs.rs/tauri-plugin-haptics) Haptic feedback and vibrations on Android and iOS. There are no standards/requirements for vibration support on Android, so the feedback APIs may not work correctly on more affordable phones, including recently released ones. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the haptics plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add haptics
    ```
 * yarn 
    ```sh
    yarn run tauri add haptics
    ```
 * pnpm 
    ```sh
    pnpm tauri add haptics
    ```
 * deno 
    ```sh
    deno task tauri add haptics
    ```
 * bun 
    ```sh
    bun tauri add haptics
    ```
 * cargo 
    ```sh
    cargo tauri add haptics
    ```
 * Manual 
  ```sh
  npm run tauri add haptics
  ```
 * npm 
  ```sh
  yarn run tauri add haptics
  ```
 * yarn 
  ```sh
  pnpm tauri add haptics
  ```
 * pnpm 
  ```sh
  deno task tauri add haptics
  ```
 * deno 
  ```sh
  bun tauri add haptics
  ```
 * bun 
  ```sh
  cargo tauri add haptics
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-haptics --target 'cfg(any(target_os = "android", target_os = "ios"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(mobile)]
                 +app.handle().plugin(tauri_plugin_haptics::init());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-haptics
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-haptics
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-haptics
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-haptics
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-haptics
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-haptics
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-haptics
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-haptics
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-haptics
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-haptics
  ```
 ## Usage The haptics plugin is available in JavaScript. 
```javascript
import {
  vibrate,
  impactFeedback,
  notificationFeedback,
  selectionFeedback,
} from '@tauri-apps/plugin-haptics';


await vibrate(1);
await impactFeedback('medium');
await notificationFeedback('warning');
await selectionFeedback();
```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/mobile.json 
```diff
{
  "$schema": "../gen/schemas/mobile-schema.json",
  "identifier": "mobile-capability",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": [
    +"haptics:allow-impact-feedback",
    +"haptics:allow-notification-feedback",
    +"haptics:allow-selection-feedback",
    +"haptics:allow-vibrate"
  ]
}
```
 ## [Permission Table](#permission-table) | Identifier | Description | | ------------------------------------- | --------------------------------------------------------------------------- | | `haptics:allow-impact-feedback` | Enables the impact_feedback command without any pre-configured scope. | | `haptics:deny-impact-feedback` | Denies the impact_feedback command without any pre-configured scope. | | `haptics:allow-notification-feedback` | Enables the notification_feedback command without any pre-configured scope. | | `haptics:deny-notification-feedback` | Denies the notification_feedback command without any pre-configured scope. | | `haptics:allow-selection-feedback` | Enables the selection_feedback command without any pre-configured scope. | | `haptics:deny-selection-feedback` | Denies the selection_feedback command without any pre-configured scope. | | `haptics:allow-vibrate` | Enables the vibrate command without any pre-configured scope. | | `haptics:deny-vibrate` | Denies the vibrate command without any pre-configured scope. |

# HTTP Client

> Access the HTTP client written in Rust.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/http)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-http)[crates.io](https://crates.io/crates/tauri-plugin-http) API Reference:[](/reference/javascript/http/)[](https://docs.rs/tauri-plugin-http) Make HTTP requests with the http plugin. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the http plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add http
    ```
 * yarn 
    ```sh
    yarn run tauri add http
    ```
 * pnpm 
    ```sh
    pnpm tauri add http
    ```
 * deno 
    ```sh
    deno task tauri add http
    ```
 * bun 
    ```sh
    bun tauri add http
    ```
 * cargo 
    ```sh
    cargo tauri add http
    ```
 * Manual 
  ```sh
  npm run tauri add http
  ```
 * npm 
  ```sh
  yarn run tauri add http
  ```
 * yarn 
  ```sh
  pnpm tauri add http
  ```
 * pnpm 
  ```sh
  deno task tauri add http
  ```
 * deno 
  ```sh
  bun tauri add http
  ```
 * bun 
  ```sh
  cargo tauri add http
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-http
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_http::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. If you’d like to make http requests in JavaScript then install the npm package as well: * npm 
       ```sh
       npm install @tauri-apps/plugin-http
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-http
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-http
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-http
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-http
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-http
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-http
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-http
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-http
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-http
  ```
 ## Usage The HTTP plugin is available in both Rust as a [reqwest](https://docs.rs/reqwest/) re-export and JavaScript. ### JavaScript 1. Configure the allowed URLs src-tauri/capabilities/default.json 
   ```json
   {
     "permissions": [
       {
         "identifier": "http:default",
         "allow": [{ "url": "https://*.tauri.app" }],
         "deny": [{ "url": "https://private.tauri.app" }]
       }
     ]
   }
   ```
 For more information, please see the documentation for [Permissions Overview](/security/permissions/) 2. Send a request The `fetch` method tries to be as close and compliant to the [`fetch` Web API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API) as possible. 
   ```javascript
   import { fetch } from '@tauri-apps/plugin-http';


   // Send a GET request
   const response = await fetch('http://test.tauri.app/data.json', {
     method: 'GET',
   });
   console.log(response.status); // e.g. 200
   console.log(response.statusText); // e.g. "OK"
   ```
 Note [Forbidden request headers](https://fetch.spec.whatwg.org/#terminology-headers) are ignored by default. To use them you must enable the `unsafe-headers` feature flag: src-tauri/Cargo.toml 
   ```toml
   [dependencies]
   tauri-plugin-http = { version = "2", features = ["unsafe-headers"] }
   ```
 ### Rust In Rust you can utilize the `reqwest` crate re-exported by the plugin. For more details refer to [reqwest docs](https://docs.rs/reqwest/). 
```rust
use tauri_plugin_http::reqwest;


let res = reqwest::get("http://my.api.host/data.json").await;
println!("{:?}", res.status()); // e.g. 200
println!("{:?}", res.text().await); // e.g Ok("{ Content }")
```
 ## [Default Permission](#default-permission) This permission set configures what kind of fetch operations are available from the http plugin. This enables all fetch operations but does not allow explicitly any origins to be fetched. This needs to be manually configured before usage. #### [Granted Permissions](#granted-permissions) All fetch operations are enabled. #### This default permission set includes the following: * `allow-fetch` * `allow-fetch-cancel` * `allow-fetch-send` * `allow-fetch-read-body` * `allow-fetch-cancel-body` ## Permission Table | Identifier | Description | | ------------------------------ | ----------------------------------------------------------------------- | | `http:allow-fetch` | Enables the fetch command without any pre-configured scope. | | `http:deny-fetch` | Denies the fetch command without any pre-configured scope. | | `http:allow-fetch-cancel` | Enables the fetch_cancel command without any pre-configured scope. | | `http:deny-fetch-cancel` | Denies the fetch_cancel command without any pre-configured scope. | | `http:allow-fetch-cancel-body` | Enables the fetch_cancel_body command without any pre-configured scope. | | `http:deny-fetch-cancel-body` | Denies the fetch_cancel_body command without any pre-configured scope. | | `http:allow-fetch-read-body` | Enables the fetch_read_body command without any pre-configured scope. | | `http:deny-fetch-read-body` | Denies the fetch_read_body command without any pre-configured scope. | | `http:allow-fetch-send` | Enables the fetch_send command without any pre-configured scope. | | `http:deny-fetch-send` | Denies the fetch_send command without any pre-configured scope. |

# Localhost

> Use a localhost server in production apps.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/localhost)[crates.io](https://crates.io/crates/tauri-plugin-localhost) API Reference:[](https://docs.rs/tauri-plugin-localhost) Expose your app’s assets through a localhost server instead of the default custom protocol. Caution This plugin brings considerable security risks and you should only use it if you know what you are doing. If in doubt, use the default custom protocol implementation. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the localhost plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add localhost
    ```
 * yarn 
    ```sh
    yarn run tauri add localhost
    ```
 * pnpm 
    ```sh
    pnpm tauri add localhost
    ```
 * deno 
    ```sh
    deno task tauri add localhost
    ```
 * bun 
    ```sh
    bun tauri add localhost
    ```
 * cargo 
    ```sh
    cargo tauri add localhost
    ```
 * Manual 
  ```sh
  npm run tauri add localhost
  ```
 * npm 
  ```sh
  yarn run tauri add localhost
  ```
 * yarn 
  ```sh
  pnpm tauri add localhost
  ```
 * pnpm 
  ```sh
  deno task tauri add localhost
  ```
 * deno 
  ```sh
  bun tauri add localhost
  ```
 * bun 
  ```sh
  cargo tauri add localhost
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-localhost
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_localhost::Builder::new().build())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 ## Usage The localhost plugin is available in Rust. src-tauri/src/lib.rs 
```rust
use tauri::{webview::WebviewWindowBuilder, WebviewUrl};


pub fn run() {
  let port: u16 = 9527;


  tauri::Builder::default()
      .plugin(tauri_plugin_localhost::Builder::new(port).build())
      .setup(move |app| {
          let url = format!("http://localhost:{}", port).parse().unwrap();
          WebviewWindowBuilder::new(app, "main".to_string(), WebviewUrl::External(url))
              .title("Localhost Example")
              .build()?;
          Ok(())
      })
      .run(tauri::generate_context!())
      .expect("error while running tauri application");
}
```

# Logging

> Configurable logging.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/log)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-log)[crates.io](https://crates.io/crates/tauri-plugin-log) API Reference:[](/reference/javascript/log/)[](https://docs.rs/tauri-plugin-log) Configurable logging for your Tauri app. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the log plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add log
    ```
 * yarn 
    ```sh
    yarn run tauri add log
    ```
 * pnpm 
    ```sh
    pnpm tauri add log
    ```
 * deno 
    ```sh
    deno task tauri add log
    ```
 * bun 
    ```sh
    bun tauri add log
    ```
 * cargo 
    ```sh
    cargo tauri add log
    ```
 * Manual 
  ```sh
  npm run tauri add log
  ```
 * npm 
  ```sh
  yarn run tauri add log
  ```
 * yarn 
  ```sh
  pnpm tauri add log
  ```
 * pnpm 
  ```sh
  deno task tauri add log
  ```
 * deno 
  ```sh
  bun tauri add log
  ```
 * bun 
  ```sh
  cargo tauri add log
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-log
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_log::Builder::new().build())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-log
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-log
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-log
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-log
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-log
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-log
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-log
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-log
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-log
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-log
  ```
 ## Usage 1. First, you need to register the plugin with Tauri. src-tauri/src/lib.rs 
   ```rust
   use tauri_plugin_log::{Target, TargetKind};


   #[cfg_attr(mobile, tauri::mobile_entry_point)]
   pub fn run() {
       tauri::Builder::default()
           .plugin(tauri_plugin_log::Builder::new().build())
           .run(tauri::generate_context!())
           .expect("error while running tauri application");
   }
   ```
 2. Afterwards, all the plugin’s APIs are available through the JavaScript guest bindings: 
   ```javascript
   import {
     warn,
     debug,
     trace,
     info,
     error,
     attachConsole,
     attachLogger,
   } from '@tauri-apps/plugin-log';
   // when using `"withGlobalTauri": true`, you may use
   // const { warn, debug, trace, info, error, attachConsole, attachLogger } = window.__TAURI__.log;
   ```
 ## Logging * JavaScript Use one of the plugin’s `warn`, `debug`, `trace`, `info` or `error` APIs to produce a log record from JavaScript code: 
  ```js
  import { warn, debug, trace, info, error } from '@tauri-apps/plugin-log';


  trace('Trace');
  info('Info');
  error('Error');
  ```
 To automatically forward all `console` messages to the log plugin you can rewrite them: 
  ```ts
  import { warn, debug, trace, info, error } from '@tauri-apps/plugin-log';


  function forwardConsole(
    fnName: 'log' | 'debug' | 'info' | 'warn' | 'error',
    logger: (message: string) => Promise<void>
  ) {
    const original = console[fnName];
    console[fnName] = (message) => {
      original(message);
      logger(message);
    };
  }


  forwardConsole('log', trace);
  forwardConsole('debug', debug);
  forwardConsole('info', info);
  forwardConsole('warn', warn);
  forwardConsole('error', error);
  ```
 * Rust To create your own logs on the Rust side you can use the [`log` crate](https://crates.io/crates/log): 
  ```rust
  log::error!("something bad happened!");
  log::info!("Tauri is awesome!");
  ```
 Note that the [`log` crate](https://crates.io/crates/log) must be added to your `Cargo.toml` file: 
  ```toml
  [dependencies]
  log = "0.4"
  ```
 ## Log targets The log plugin builder has a `targets` function that lets you configure common destination of all your application logs. Note By default the plugin logs to stdout and to a file in the application logs directory. To only use your own log targets, call `clear_targets`: 
```rust
tauri_plugin_log::Builder::new()
.clear_targets()
.build()
```
 ### Printing logs to the terminal To forward all your logs to the terminal, enable the `Stdout` or `Stderr` targets: 
```rust
tauri_plugin_log::Builder::new()
  .target(tauri_plugin_log::Target::new(
    tauri_plugin_log::TargetKind::Stdout,
  ))
  .build()
```
 This target is enabled by default. ### Logging to the webview console To view all your Rust logs in the webview console, enable the `Webview` target and run `attachConsole` in your frontend: 
```rust
tauri_plugin_log::Builder::new()
  .target(tauri_plugin_log::Target::new(
    tauri_plugin_log::TargetKind::Webview,
  ))
  .build()
```
 
```js
import { attachConsole } from '@tauri-apps/plugin-log';
const detach = await attachConsole();
// call detach() if you do not want to print logs to the console anymore
```
 ### Persisting logs To write all logs to a file, you can use either the `LogDir` or the `Folder` targets. * `LogDir`: 
```rust
tauri_plugin_log::Builder::new()
  .target(tauri_plugin_log::Target::new(
    tauri_plugin_log::TargetKind::LogDir {
      file_name: Some("logs".to_string()),
    },
  ))
  .build()
```
 When using the LogDir target, all logs are stored in the recommended log directory. The following table describes the location of the logs per platform: | Platform | Value | Example | | -------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------- | | Linux | `$XDG_DATA_HOME/{bundleIdentifier}/logs` or `$HOME/.local/share/{bundleIdentifier}/logs` | `/home/alice/.local/share/com.tauri.dev/logs` | | macOS | `{homeDir}/Library/Logs/{bundleIdentifier}` | `/Users/Alice/Library/Logs/com.tauri.dev` | | Windows | `{FOLDERID_LocalAppData}/{bundleIdentifier}/logs` | `C:\Users\Alice\AppData\Local\com.tauri.dev\logs` | * `Folder`: The Folder target lets you write logs to a custom location in the filesystem. 
```rust
tauri_plugin_log::Builder::new()
  .target(tauri_plugin_log::Target::new(
    tauri_plugin_log::TargetKind::Folder {
      path: std::path::PathBuf::from("/path/to/logs"),
      file_name: None,
    },
  ))
  .build()
```
 The default `file_name` is the application name. #### Configuring log file behavior By default the log file gets discarded when it reaches the maximum size. The maximum file size can be configured via the builder’s `max_file_size` function: 
```rust
tauri_plugin_log::Builder::new()
  .max_file_size(50_000 /* bytes */)
  .build()
```
 Tauri can automatically rotate your log file when it reaches the size limit instead of discarding the previous file. This behavior can be configured using `rotation_strategy`: 
```rust
tauri_plugin_log::Builder::new()
  .rotation_strategy(tauri_plugin_log::RotationStrategy::KeepAll)
  .build()
```
 ### Filtering By default **all** logs are processed. There are some mechanisms to reduce the amount of logs and filter only relevant information. ### Maximum log level To set a maximum log level, use the `level` function: 
```rust
tauri_plugin_log::Builder::new()
  .level(log::LevelFilter::Info)
  .build()
```
 In this example, debug and trace logs are discarded as they have a lower level than *info*. It is also possible to define separate maximum levels for individual modules: 
```rust
tauri_plugin_log::Builder::new()
  .level(log::LevelFilter::Info)
  // verbose logs only for the commands module
  .level_for("my_crate_name::commands", log::LevelFilter::Trace)
  .build()
```
 Note that these APIs use the [`log` crate](https://crates.io/crates/log), which must be added to your `Cargo.toml` file: 
```toml
[dependencies]
log = "0.4"
```
 ### Target filter A `filter` function can be defined to discard unwanted logs by checking their metadata: 
```rust
tauri_plugin_log::Builder::new()
  // exclude logs with target `"hyper"`
  .filter(|metadata| metadata.target() != "hyper")
  .build()
```
 ### Formatting The log plugin formats each log record as `DATE[TARGET][LEVEL] MESSAGE`. A custom format function can be provided with `format`: 
```rust
tauri_plugin_log::Builder::new()
  .format(|out, message, record| {
    out.finish(format_args!(
      "[{} {}] {}",
      record.level(),
      record.target(),
      message
    ))
  })
  .build()
```
 ### Applying a different format to targets You can specify your own log format for specific targets by using the `format` method on `tauri_plugin_log::Target`. You may also wish to call `clear_format` on the builder to remove the default formatter, which is applied to all targets: 
```rust
tauri_plugin_log::Builder::new()
    .clear_format()
    .targets([
        tauri_plugin_log::Target::new(
            tauri_plugin_log::TargetKind::Stdout
        )
        .format(move |out, message, record| {
            // custom formatter for stdout
        }),
        tauri_plugin_log::Target::new(
            tauri_plugin_log::TargetKind::LogDir { file_name: None }
        )
        .format(move |out, message, record| {
            // custom formatter for log files
        }),
    ])
    .build(),
```
 #### Log dates By default the log plugin uses the UTC timezone to format dates but you can configure it to use the local timezone with `timezone_strategy`: 
```rust
tauri_plugin_log::Builder::new()
  .timezone_strategy(tauri_plugin_log::TimezoneStrategy::UseLocal)
  .build()
```
 ## Permissions By default, all plugin commands are blocked and cannot be accessed. You must define a list of permissions in your `capabilities` configuration. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  +"permissions": ["log:default"]
}
```
 ## [Default Permission](#default-permission) Allows the log command #### This default permission set includes the following: * `allow-log` ## Permission Table | Identifier | Description | | --------------- | --------------------------------------------------------- | | `log:allow-log` | Enables the log command without any pre-configured scope. | | `log:deny-log` | Denies the log command without any pre-configured scope. |

# NFC

> Read and write NFC tags on Android and iOS.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/nfc)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-nfc)[crates.io](https://crates.io/crates/tauri-plugin-nfc) API Reference:[](/reference/javascript/nfc/)[](https://docs.rs/tauri-plugin-nfc) Read and write NFC tags on Android and iOS. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the nfc plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add nfc
    ```
 * yarn 
    ```sh
    yarn run tauri add nfc
    ```
 * pnpm 
    ```sh
    pnpm tauri add nfc
    ```
 * bun 
    ```sh
    bun tauri add nfc
    ```
 * cargo 
    ```sh
    cargo tauri add nfc
    ```
 * Manual 
  ```sh
  npm run tauri add nfc
  ```
 * npm 
  ```sh
  yarn run tauri add nfc
  ```
 * yarn 
  ```sh
  pnpm tauri add nfc
  ```
 * pnpm 
  ```sh
  bun tauri add nfc
  ```
 * bun 
  ```sh
  cargo tauri add nfc
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-nfc --target 'cfg(any(target_os = "android", target_os = "ios"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(mobile)]
                 +app.handle().plugin(tauri_plugin_nfc::init());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-nfc
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-nfc
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-nfc
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-nfc
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-nfc
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-nfc
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-nfc
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-nfc
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-nfc
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-nfc
  ```
 ## Configuration The NFC plugin requires native configuration for iOS. ### iOS To access the NFC APIs on iOS you must adjust the target iOS version, configure a usage description on the Info.plist file and add the NFC capability to your application. #### Target IOS version The NFC plugin requires iOS 14+. This is the default for Tauri applications created with Tauri CLI v2.8 and above, but you can edit your Xcode project to configure it. In the `src-tauri/gen/apple/<project-name>.xcodeproj/project.pbxproj` file, set all `IPHONEOS_DEPLOYMENT_TARGET` properties to `14.0`: src-tauri/gen/apple/\<project-name>.xcodeproj/project.pbxproj 
```pbxproj
/* Begin XCBuildConfiguration section */
    1234567890ABCDEF12345678 /* release */ = {
      isa = XCBuildConfiguration;
      buildSettings = {
        /* ... */
        IPHONEOS_DEPLOYMENT_TARGET = 14.0;
      };
      name = release;
    };
    ABCDEF1234567890ABCDEF12 /* debug */ = {
      isa = XCBuildConfiguration;
      buildSettings = {
        /* ... */
        IPHONEOS_DEPLOYMENT_TARGET = 14.0;
      };
      name = debug;
    };
```
 Alternatively you can set the deployment target from Xcode in the `General > Minimum Deployments > iOS` configuration. #### Info.plist On iOS the NFC plugin requires the `NFCReaderUsageDescription` information property list value, which should describe why your app needs to scan or write to NFC tags. In the `src-tauri/Info.ios.plist` file, add the following snippet: src-tauri/Info.ios.plist 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>NFCReaderUsageDescription</key>
    <string>Read and write various NFC tags</string>
  </dict>
</plist>
```
 #### NFC Capability Additionally iOS requires the NFC capability to be associated with your application. The capability can be added in Xcode in the project configuration’s “Signing & Capabilities” tab by clicking the “+ Capability” button and selecting the “Near Field Communication Tag Reading” capability (see [Add a capability to a target](https://help.apple.com/xcode/mac/current/#/dev88ff319e7) for more information) or by adding the following configuration to the `gen/apple/<app-name>_iOS/<app-name>_iOS.entitlements` file: gen/apple/\<app-name>\_iOS/\<app-name>\_iOS.entitlements 
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.developer.nfc.readersession.formats</key>
  <array>
    <string>TAG</string>
  </array>
</dict>
</plist>
```
 ## Usage The NFC plugin is available in both JavaScript and Rust, allowing you to scan and write to NFC tags. ### Checking if NFC is supported Not every mobile device has the capability to scan NFC tags, so you should check for availability before using the scan and write APIs. * JavaScript 
  ```javascript
  import { isAvailable } from '@tauri-apps/plugin-nfc';


  const canScanNfc = await isAvailable();
  ```
 * Rust 
  ```rust
  tauri::Builder::default()
    .setup(|app| {
      #[cfg(mobile)]
      {
        use tauri_plugin_nfc::NfcExt;


        app.handle().plugin(tauri_plugin_nfc::init());


        let can_scan_nfc = app.nfc().is_available()?;
      }
      Ok(())
    })
  ```
 ### Scanning NFC tags The plugin can scan either generic NFC tags or NFC tags with a NDEF (NFC Data Exchange Format) message, which is a standard format to encapsulate typed data in an NFC tag. * JavaScript 
  ```javascript
  import { scan } from '@tauri-apps/plugin-nfc';


  const scanType = {
    type: 'ndef', // or 'tag',
  };


  const options = {
    keepSessionAlive: false,
    // configure the messages displayed in the "Scan NFC" dialog on iOS
    message: 'Scan a NFC tag',
    successMessage: 'NFC tag successfully scanned',
  };


  const tag = await scan(scanType, options);
  ```
 * Rust 
  ```rust
  tauri::Builder::default()
    .setup(|app| {
      #[cfg(mobile)]
      {
        use tauri_plugin_nfc::NfcExt;


        app.handle().plugin(tauri_plugin_nfc::init());


        let tag = app
          .nfc()
          .scan(tauri_plugin_nfc::ScanRequest {
              kind: tauri_plugin_nfc::ScanKind::Ndef {
                  mime_type: None,
                  uri: None,
                  tech_list: None,
              },
              keep_session_alive: false,
          })?
          .tag;
      }
      Ok(())
    })
  ```
 Note The `keepSessionAlive` option can be used to directly write to the scanned NFC tag later. If you do not provide that option, the session is recreated on the next `write()` call, which means the app will try to rescan the tag. #### Filters The NFC scanner can also filter tags with a specific URI format, mime type or NFC tag technologies. In this case, the scan will only detect tags that matches the provided filters. Note Filtering is only available on Android, so you should always check the scanned NFC tag contents. The mime type is case sensitive and must be provided with lower case letters. * JavaScript 
  ```javascript
  import { scan, TechKind } from '@tauri-apps/plugin-nfc';


  const techLists = [
    // capture anything using NfcF
    [TechKind.NfcF],
    // capture all MIFARE Classics with NDEF payloads
    [TechKind.NfcA, TechKind.MifareClassic, TechKind.Ndef],
  ];


  const tag = await scan({
    type: 'ndef', // or 'tag'
    mimeType: 'text/plain',
    uri: {
      scheme: 'https',
      host: 'my.domain.com',
      pathPrefix: '/app',
    },
    techLists,
  });
  ```
 * Rust 
  ```rust
  tauri::Builder::default()
    .setup(|app| {
      #[cfg(mobile)]
      {
        use tauri_plugin_nfc::NfcExt;


        app.handle().plugin(tauri_plugin_nfc::init());


        let tag = app
          .nfc()
          .scan(tauri_plugin_nfc::ScanRequest {
              kind: tauri_plugin_nfc::ScanKind::Ndef {
                  mime_type: Some("text/plain".to_string()),
                  uri: Some(tauri_plugin_nfc::UriFilter {
                    scheme: Some("https".to_string()),
                    host: Some("my.domain.com".to_string()),
                    path_prefix: Some("/app".to_string()),
                  }),
                  tech_list: Some(vec![
                    vec![tauri_plugin_nfc::TechKind::Ndef],
                  ]),
              },
          })?
          .tag;
      }
      Ok(())
    })
  ```
 ### Writing to NFC tags The `write` API can be used to write a payload to a NFC tag. If there’s no scanned tag with `keepSessionAlive: true`, the application will first scan an NFC tag. * JavaScript 
  ```javascript
  import { write, textRecord, uriRecord } from '@tauri-apps/plugin-nfc';


  const payload = [uriRecord('https://tauri.app'), textRecord('some payload')];


  const options = {
    // the kind is only required if you do not have a scanned tag session alive
    // its format is the same as the argument provided to scan()
    kind: {
      type: 'ndef',
    },
    // configure the messages displayed in the "Scan NFC" dialog on iOS
    message: 'Scan a NFC tag',
    successfulReadMessage: 'NFC tag successfully scanned',
    successMessage: 'NFC tag successfully written',
  };


  await write(payload, options);
  ```
 * Rust Caution The Rust API currently only provides a low level interface for writing NFC payloads. The API will be enhanced soon. 
  ```rust
  tauri::Builder::default()
    .setup(|app| {
      #[cfg(mobile)]
      {
        use tauri_plugin_nfc::NfcExt;


        app.handle().plugin(tauri_plugin_nfc::init());


        app
          .nfc()
          .write(vec![
            tauri_plugin_nfc::NfcRecord {
              format: tauri_plugin_nfc::NFCTypeNameFormat::NfcWellKnown,
              kind: vec![0x55], // URI record
              id: vec![],
              payload: vec![], // insert payload here
            }
          ])?;
      }
      Ok(())
    })
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    ...,
    +"nfc:default",
  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures what kind of operations are available from the nfc plugin. #### [Granted Permissions](#granted-permissions) Checking if the NFC functionality is available and scanning nearby tags is allowed. Writing to tags needs to be manually enabled. #### This default permission set includes the following: * `allow-is-available` * `allow-scan` ## Permission Table | Identifier | Description | | ------------------------ | ------------------------------------------------------------------ | | `nfc:allow-is-available` | Enables the is_available command without any pre-configured scope. | | `nfc:deny-is-available` | Denies the is_available command without any pre-configured scope. | | `nfc:allow-scan` | Enables the scan command without any pre-configured scope. | | `nfc:deny-scan` | Denies the scan command without any pre-configured scope. | | `nfc:allow-write` | Enables the write command without any pre-configured scope. | | `nfc:deny-write` | Denies the write command without any pre-configured scope. |

# Notifications

> Send native notifications to the user.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/notification)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-notification)[crates.io](https://crates.io/crates/tauri-plugin-notification) API Reference:[](/reference/javascript/notification/)[](https://docs.rs/tauri-plugin-notification) Send native notifications to your user using the notification plugin. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | --------------------------------------------------------------------------- | | windows | | Only works for installed apps. Shows powershell name & icon in development. | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the notifications plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add notification
    ```
 * yarn 
    ```sh
    yarn run tauri add notification
    ```
 * pnpm 
    ```sh
    pnpm tauri add notification
    ```
 * deno 
    ```sh
    deno task tauri add notification
    ```
 * bun 
    ```sh
    bun tauri add notification
    ```
 * cargo 
    ```sh
    cargo tauri add notification
    ```
 * Manual 
  ```sh
  npm run tauri add notification
  ```
 * npm 
  ```sh
  yarn run tauri add notification
  ```
 * yarn 
  ```sh
  pnpm tauri add notification
  ```
 * pnpm 
  ```sh
  deno task tauri add notification
  ```
 * deno 
  ```sh
  bun tauri add notification
  ```
 * bun 
  ```sh
  cargo tauri add notification
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-notification
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_notification::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. If you’d like to use notifications in JavaScript then install the npm package as well: * npm 
       ```sh
       npm install @tauri-apps/plugin-notification
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-notification
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-notification
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-notification
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-notification
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-notification
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-notification
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-notification
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-notification
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-notification
  ```
 ## Usage Here are a few examples of how to use the notification plugin: * [Send notification to users](#send-notification) * [Add an action to a notification](#actions) * [Add an attachment to a notification](#attachments) * [Send a notification in a specific channel](#channels) The notification plugin is available in both JavaScript and Rust. ### Send Notification Follow these steps to send a notification: 1. Check if permission is granted 2. Request permission if not granted 3. Send the notification * JavaScript 
  ```javascript
  import {
    isPermissionGranted,
    requestPermission,
    sendNotification,
  } from '@tauri-apps/plugin-notification';
  // when using `"withGlobalTauri": true`, you may use
  // const { isPermissionGranted, requestPermission, sendNotification, } = window.__TAURI__.notification;


  // Do you have permission to send a notification?
  let permissionGranted = await isPermissionGranted();


  // If not we need to request it
  if (!permissionGranted) {
    const permission = await requestPermission();
    permissionGranted = permission === 'granted';
  }


  // Once permission has been granted we can send the notification
  if (permissionGranted) {
    sendNotification({ title: 'Tauri', body: 'Tauri is awesome!' });
  }
  ```
 * Rust 
  ```rust
  tauri::Builder::default()
      .plugin(tauri_plugin_notification::init())
      .setup(|app| {
          use tauri_plugin_notification::NotificationExt;
          app.notification()
              .builder()
              .title("Tauri")
              .body("Tauri is awesome")
              .show()
              .unwrap();


          Ok(())
      })
      .run(tauri::generate_context!())
      .expect("error while running tauri application");
  ```
 ### Actions Mobile Only The Actions API is only available on mobile platforms. Actions add interactive buttons and inputs to notifications. Use them to create a responsive experience for your users. #### Register Action Types Register action types to define interactive elements: 
```javascript
import { registerActionTypes } from '@tauri-apps/plugin-notification';


await registerActionTypes([
  {
    id: 'messages',
    actions: [
      {
        id: 'reply',
        title: 'Reply',
        input: true,
        inputButtonTitle: 'Send',
        inputPlaceholder: 'Type your reply...',
      },
      {
        id: 'mark-read',
        title: 'Mark as Read',
        foreground: false,
      },
    ],
  },
]);
```
 #### Action Properties | Property | Description | | ------------------------ | --------------------------------------- | | `id` | Unique identifier for the action | | `title` | Display text for the action button | | `requiresAuthentication` | Requires device authentication | | `foreground` | Brings app to foreground when triggered | | `destructive` | Shows action in red on iOS | | `input` | Enables text input | | `inputButtonTitle` | Text for input submit button | | `inputPlaceholder` | Placeholder text for input field | #### Listen for Actions Listen to user interactions with notification actions: 
```javascript
import { onAction } from '@tauri-apps/plugin-notification';


await onAction((notification) => {
  console.log('Action performed:', notification);
});
```
 ### Attachments Attachments add media content to notifications. Support varies by platform. 
```javascript
import { sendNotification } from '@tauri-apps/plugin-notification';


sendNotification({
  title: 'New Image',
  body: 'Check out this picture',
  attachments: [
    {
      id: 'image-1',
      url: 'asset:///notification-image.jpg',
    },
  ],
});
```
 #### Attachment Properties | Property | Description | | -------- | ---------------------------------------------- | | `id` | Unique identifier | | `url` | Content URL using asset:// or file:// protocol | Note: Test attachments on your target platforms to ensure compatibility. ### Channels Channels organize notifications into categories with different behaviors. While primarily used on Android, they provide a consistent API across platforms. #### Create a Channel 
```javascript
import {
  createChannel,
  Importance,
  Visibility,
} from '@tauri-apps/plugin-notification';


await createChannel({
  id: 'messages',
  name: 'Messages',
  description: 'Notifications for new messages',
  importance: Importance.High,
  visibility: Visibility.Private,
  lights: true,
  lightColor: '#ff0000',
  vibration: true,
  sound: 'notification_sound',
});
```
 #### Channel Properties | Property | Description | | ------------- | ---------------------------------------------- | | `id` | Unique identifier | | `name` | Display name | | `description` | Purpose description | | `importance` | Priority level (None, Min, Low, Default, High) | | `visibility` | Privacy setting (Secret, Private, Public) | | `lights` | Enable notification LED (Android) | | `lightColor` | LED color (Android) | | `vibration` | Enable vibrations | | `sound` | Custom sound filename | #### Managing Channels List existing channels: 
```javascript
import { channels } from '@tauri-apps/plugin-notification';


const existingChannels = await channels();
```
 Remove a channel: 
```javascript
import { removeChannel } from '@tauri-apps/plugin-notification';


await removeChannel('messages');
```
 #### Using Channels Send a notification using a channel: 
```javascript
import { sendNotification } from '@tauri-apps/plugin-notification';


sendNotification({
  title: 'New Message',
  body: 'You have a new message',
  channelId: 'messages',
});
```
 Note: Create channels before sending notifications that reference them. Invalid channel IDs prevent notifications from displaying. ## Security Considerations Aside from normal sanitization procedures of user input there are currently no known security considerations. ## [Default Permission](#default-permission) This permission set configures which notification features are by default exposed. #### [Granted Permissions](#granted-permissions) It allows all notification related features. #### This default permission set includes the following: * `allow-is-permission-granted` * `allow-request-permission` * `allow-notify` * `allow-register-action-types` * `allow-register-listener` * `allow-remove-listener` * `allow-cancel` * `allow-get-pending` * `allow-remove-active` * `allow-get-active` * `allow-check-permissions` * `allow-show` * `allow-batch` * `allow-list-channels` * `allow-delete-channel` * `allow-create-channel` * `allow-permission-state` ## Permission Table | Identifier | Description | | ------------------------------------------ | --------------------------------------------------------------------------- | | `notification:allow-batch` | Enables the batch command without any pre-configured scope. | | `notification:deny-batch` | Denies the batch command without any pre-configured scope. | | `notification:allow-cancel` | Enables the cancel command without any pre-configured scope. | | `notification:deny-cancel` | Denies the cancel command without any pre-configured scope. | | `notification:allow-check-permissions` | Enables the check_permissions command without any pre-configured scope. | | `notification:deny-check-permissions` | Denies the check_permissions command without any pre-configured scope. | | `notification:allow-create-channel` | Enables the create_channel command without any pre-configured scope. | | `notification:deny-create-channel` | Denies the create_channel command without any pre-configured scope. | | `notification:allow-delete-channel` | Enables the delete_channel command without any pre-configured scope. | | `notification:deny-delete-channel` | Denies the delete_channel command without any pre-configured scope. | | `notification:allow-get-active` | Enables the get_active command without any pre-configured scope. | | `notification:deny-get-active` | Denies the get_active command without any pre-configured scope. | | `notification:allow-get-pending` | Enables the get_pending command without any pre-configured scope. | | `notification:deny-get-pending` | Denies the get_pending command without any pre-configured scope. | | `notification:allow-is-permission-granted` | Enables the is_permission_granted command without any pre-configured scope. | | `notification:deny-is-permission-granted` | Denies the is_permission_granted command without any pre-configured scope. | | `notification:allow-list-channels` | Enables the list_channels command without any pre-configured scope. | | `notification:deny-list-channels` | Denies the list_channels command without any pre-configured scope. | | `notification:allow-notify` | Enables the notify command without any pre-configured scope. | | `notification:deny-notify` | Denies the notify command without any pre-configured scope. | | `notification:allow-permission-state` | Enables the permission_state command without any pre-configured scope. | | `notification:deny-permission-state` | Denies the permission_state command without any pre-configured scope. | | `notification:allow-register-action-types` | Enables the register_action_types command without any pre-configured scope. | | `notification:deny-register-action-types` | Denies the register_action_types command without any pre-configured scope. | | `notification:allow-register-listener` | Enables the register_listener command without any pre-configured scope. | | `notification:deny-register-listener` | Denies the register_listener command without any pre-configured scope. | | `notification:allow-remove-active` | Enables the remove_active command without any pre-configured scope. | | `notification:deny-remove-active` | Denies the remove_active command without any pre-configured scope. | | `notification:allow-remove-listener` | Enables the remove_listener command without any pre-configured scope. | | `notification:deny-remove-listener` | Denies the remove_listener command without any pre-configured scope. | | `notification:allow-request-permission` | Enables the request_permission command without any pre-configured scope. | | `notification:deny-request-permission` | Denies the request_permission command without any pre-configured scope. | | `notification:allow-show` | Enables the show command without any pre-configured scope. | | `notification:deny-show` | Denies the show command without any pre-configured scope. |

# Opener

> Open files and URLs in external applications.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/opener)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-opener)[crates.io](https://crates.io/crates/tauri-plugin-opener) API Reference:[](/reference/javascript/opener/)[](https://docs.rs/tauri-plugin-opener) This plugin allows you to open files and URLs in a specified, or the default, application. It also supports “revealing” files in the system’s file explorer. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----------------------------------- | | windows | | | | linux | | | | macos | | | | android | | Only allows to open URLs via `open` | | ios | | Only allows to open URLs via `open` | ## Setup Install the opener plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add opener
    ```
 * yarn 
    ```sh
    yarn run tauri add opener
    ```
 * pnpm 
    ```sh
    pnpm tauri add opener
    ```
 * deno 
    ```sh
    deno task tauri add opener
    ```
 * bun 
    ```sh
    bun tauri add opener
    ```
 * cargo 
    ```sh
    cargo tauri add opener
    ```
 * Manual 
  ```sh
  npm run tauri add opener
  ```
 * npm 
  ```sh
  yarn run tauri add opener
  ```
 * yarn 
  ```sh
  pnpm tauri add opener
  ```
 * pnpm 
  ```sh
  deno task tauri add opener
  ```
 * deno 
  ```sh
  bun tauri add opener
  ```
 * bun 
  ```sh
  cargo tauri add opener
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-opener
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_opener::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-opener
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-opener
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-opener
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-opener
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-opener
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-opener
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-opener
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-opener
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-opener
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-opener
  ```
 ## Usage The opener plugin is available in both JavaScript and Rust. * JavaScript 
  ```javascript
  import { openPath, openUrl } from '@tauri-apps/plugin-opener';
  // when using `"withGlobalTauri": true`, you may use
  // const { openPath } = window.__TAURI__.opener;


  // opens a file using the default program:
  await openPath('/path/to/file');
  // opens a file using `vlc` command on Windows:
  await openPath('C:/path/to/file', 'vlc');
  // opens a URL using the default program:
  await openUrl('https://tauri.app');
  ```
 * Rust Note that `app` is an instance of `App` or [`AppHandle`](https://docs.rs/tauri/2.0.0/tauri/struct.AppHandle.html). 
  ```rust
  use tauri_plugin_opener::OpenerExt;


  // opens a file using the default program:
  app.opener().open_path("/path/to/file", None::<&str>);
  // opens a file using `vlc` command on Windows:
  app.opener().open_path("C:/path/to/file", Some("vlc"));
  // opens a URL using the default program:
  app.opener().open_url("https://tauri.app", None::<&str>);
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. Below are two example scope configurations. Both `path` and `url` use the [glob pattern syntax](https://docs.rs/glob/latest/glob/struct.Pattern.html) to define allowed file paths and URLs. First, an example on how to add permissions to specific paths for the `openPath()` function: src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  +"permissions": [
+    {
      +"identifier": "opener:allow-open-path",
      +"allow": [
+        {
          +"path": "/path/to/file"
+        },
+        {
          +"path": "$APPDATA/file"
+        }
      ]
    }
  ]
}
```
 Lastly, an example on how to add permissions for the exact `https://tauri.app` URL and all URLs on a custom protocol (must be known to the OS) for the `openUrl()` function: src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  +"permissions": [
+    {
      +"identifier": "opener:allow-open-url",
      +"allow": [
+        {
          +"url": "https://tauri.app"
+        },
+        {
          +"url": "custom:*"
+        }
      ]
    }
  ]
}
```
 ## [Default Permission](#default-permission) This permission set allows opening `mailto:`, `tel:`, `https://` and `http://` urls using their default application as well as reveal file in directories using default file explorer #### This default permission set includes the following: * `allow-open-url` * `allow-reveal-item-in-dir` * `allow-default-urls` ## Permission Table | Identifier | Description | | --------------------------------- | ------------------------------------------------------------------------------------------------------ | | `opener:allow-default-urls` | This enables opening `mailto:`, `tel:`, `https://` and `http://` urls using their default application. | | `opener:allow-open-path` | Enables the open_path command without any pre-configured scope. | | `opener:deny-open-path` | Denies the open_path command without any pre-configured scope. | | `opener:allow-open-url` | Enables the open_url command without any pre-configured scope. | | `opener:deny-open-url` | Denies the open_url command without any pre-configured scope. | | `opener:allow-reveal-item-in-dir` | Enables the reveal_item_in_dir command without any pre-configured scope. | | `opener:deny-reveal-item-in-dir` | Denies the reveal_item_in_dir command without any pre-configured scope. |

# OS Information

> Read information about the operating system.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/os)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-os)[crates.io](https://crates.io/crates/tauri-plugin-os) API Reference:[](/reference/javascript/os/)[](https://docs.rs/tauri-plugin-os) Read information about the operating system using the OS Information plugin. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the OS Information plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add os
    ```
 * yarn 
    ```sh
    yarn run tauri add os
    ```
 * pnpm 
    ```sh
    pnpm tauri add os
    ```
 * deno 
    ```sh
    deno task tauri add os
    ```
 * bun 
    ```sh
    bun tauri add os
    ```
 * cargo 
    ```sh
    cargo tauri add os
    ```
 * Manual 
  ```sh
  npm run tauri add os
  ```
 * npm 
  ```sh
  yarn run tauri add os
  ```
 * yarn 
  ```sh
  pnpm tauri add os
  ```
 * pnpm 
  ```sh
  deno task tauri add os
  ```
 * deno 
  ```sh
  bun tauri add os
  ```
 * bun 
  ```sh
  cargo tauri add os
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-os
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_os::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. If you’d like to use in JavaScript then install the npm package as well: * npm 
       ```sh
       npm install @tauri-apps/plugin-os
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-os
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-os
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-os
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-os
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-os
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-os
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-os
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-os
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-os
  ```
 ## Usage With this plugin you can query multiple information from current operational system. See all available functions in the [JavaScript API](/reference/javascript/os/) or [Rust API](https://docs.rs/tauri-plugin-os/) references. #### Example: OS Platform `platform` returns a string describing the specific operating system in use. The value is set at compile time. Possible values are `linux`, `macos`, `ios`, `freebsd`, `dragonfly`, `netbsd`, `openbsd`, `solaris`, `android`, `windows`. * JavaScript 
  ```javascript
  import { platform } from '@tauri-apps/plugin-os';
  // when using `"withGlobalTauri": true`, you may use
  // const { platform } = window.__TAURI__.os;


  const currentPlatform = platform();
  console.log(currentPlatform);
  // Prints "windows" to the console
  ```
 * Rust 
  ```rust
  let platform = tauri_plugin_os::platform();
  println!("Platform: {}", platform);
  // Prints "windows" to the terminal
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    ...,
    +"os:default"
  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures which operating system information are available to gather from the frontend. #### [Granted Permissions](#granted-permissions) All information except the host name are available. #### This default permission set includes the following: * `allow-arch` * `allow-exe-extension` * `allow-family` * `allow-locale` * `allow-os-type` * `allow-platform` * `allow-version` ## Permission Table | Identifier | Description | | ------------------------ | ------------------------------------------------------------------- | | `os:allow-arch` | Enables the arch command without any pre-configured scope. | | `os:deny-arch` | Denies the arch command without any pre-configured scope. | | `os:allow-exe-extension` | Enables the exe_extension command without any pre-configured scope. | | `os:deny-exe-extension` | Denies the exe_extension command without any pre-configured scope. | | `os:allow-family` | Enables the family command without any pre-configured scope. | | `os:deny-family` | Denies the family command without any pre-configured scope. | | `os:allow-hostname` | Enables the hostname command without any pre-configured scope. | | `os:deny-hostname` | Denies the hostname command without any pre-configured scope. | | `os:allow-locale` | Enables the locale command without any pre-configured scope. | | `os:deny-locale` | Denies the locale command without any pre-configured scope. | | `os:allow-os-type` | Enables the os_type command without any pre-configured scope. | | `os:deny-os-type` | Denies the os_type command without any pre-configured scope. | | `os:allow-platform` | Enables the platform command without any pre-configured scope. | | `os:deny-platform` | Denies the platform command without any pre-configured scope. | | `os:allow-version` | Enables the version command without any pre-configured scope. | | `os:deny-version` | Denies the version command without any pre-configured scope. |

# Persisted Scope

> Persist runtime scope changes on the filesystem.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/persisted-scope)[crates.io](https://crates.io/crates/tauri-plugin-persisted-scope) API Reference:[](https://docs.rs/tauri-plugin-persisted-scope) Save filesystem and asset scopes and restore them when the app is reopened. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the persisted-scope plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add persisted-scope
    ```
 * yarn 
    ```sh
    yarn run tauri add persisted-scope
    ```
 * pnpm 
    ```sh
    pnpm tauri add persisted-scope
    ```
 * deno 
    ```sh
    deno task tauri add persisted-scope
    ```
 * bun 
    ```sh
    bun tauri add persisted-scope
    ```
 * cargo 
    ```sh
    cargo tauri add persisted-scope
    ```
 * Manual 
  ```sh
  npm run tauri add persisted-scope
  ```
 * npm 
  ```sh
  yarn run tauri add persisted-scope
  ```
 * yarn 
  ```sh
  pnpm tauri add persisted-scope
  ```
 * pnpm 
  ```sh
  deno task tauri add persisted-scope
  ```
 * deno 
  ```sh
  bun tauri add persisted-scope
  ```
 * bun 
  ```sh
  cargo tauri add persisted-scope
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-persisted-scope
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_persisted_scope::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 Caution The `persisted-scope` plugin *must* be registered and initialized after the `fs` plugin, as illustrated by the example below: 
```rs
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init()) // fs MUST BE before persisted scope!
        .plugin(tauri_plugin_persisted_scope::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```
 **Not doing so will result in the persisted scope not working!** You should also see a warning message upon launching your app in dev mode, similar to this: 
```plaintext
Please make sure to register the `fs` plugin before the `persisted-scope` plugin!
```
 ## Usage After setup the plugin will automatically save and restore filesystem and asset scopes.

# Positioner

> Move windows to common locations.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/positioner)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-positioner)[crates.io](https://crates.io/crates/tauri-plugin-positioner) API Reference:[](/reference/javascript/positioner/)[](https://docs.rs/tauri-plugin-positioner) Position your windows at well-known locations. This plugin is a port of [electron-positioner](https://github.com/jenslind/electron-positioner) for Tauri. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the positioner plugin to get started. Note If you only intend on moving the window from Rust code, you only need the dependency in `src-tauri/Cargo.toml`, and can remove the plugin registration from `lib.rs` if you choose to setup automatically. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add positioner
    ```
 * yarn 
    ```sh
    yarn run tauri add positioner
    ```
 * pnpm 
    ```sh
    pnpm tauri add positioner
    ```
 * deno 
    ```sh
    deno task tauri add positioner
    ```
 * bun 
    ```sh
    bun tauri add positioner
    ```
 * cargo 
    ```sh
    cargo tauri add positioner
    ```
 * Manual 
  ```sh
  npm run tauri add positioner
  ```
 * npm 
  ```sh
  yarn run tauri add positioner
  ```
 * yarn 
  ```sh
  pnpm tauri add positioner
  ```
 * pnpm 
  ```sh
  deno task tauri add positioner
  ```
 * deno 
  ```sh
  bun tauri add positioner
  ```
 * bun 
  ```sh
  cargo tauri add positioner
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-positioner --target 'cfg(any(target_os = "macos", windows, target_os = "linux"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.setup(|app| {
                 #[cfg(desktop)]
                 app.handle().plugin(tauri_plugin_positioner::init());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-positioner
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-positioner
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-positioner
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-positioner
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-positioner
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-positioner
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-positioner
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-positioner
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-positioner
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-positioner
  ```
 Additional setup is required to get tray-relative positions to work. 1. Add `tray-icon` feature to your `Cargo.toml` file: src-tauri/Cargo.toml 
   ```diff
   [dependencies]
   +tauri-plugin-positioner = { version = "2.0.0", features = ["tray-icon"] }
   ```
 2. Setup `on_tray_event` for positioner plugin: src-tauri/src/lib.rs 
   ```diff
   pub fn run() {
     tauri::Builder::default()
       // This is required to get tray-relative positions to work
       +.setup(|app| {
   +        #[cfg(desktop)]
   +        {
             +app.handle().plugin(tauri_plugin_positioner::init());
   +            tauri::tray::TrayIconBuilder::new()
                 +.on_tray_icon_event(|tray_handle, event| {
   +                tauri_plugin_positioner::on_tray_event(tray_handle.app_handle(), &event);
   +              })
                 +.build(app)?;
           }
         Ok(())
       })
       .run(tauri::generate_context!())
       .expect("error while running tauri application");
   }
   ```
 ## Usage The plugin’s APIs are available through the JavaScript guest bindings: 
```javascript
import { moveWindow, Position } from '@tauri-apps/plugin-positioner';
// when using `"withGlobalTauri": true`, you may use
// const { moveWindow, Position } = window.__TAURI__.positioner;


moveWindow(Position.TopRight);
```
 You can import and use the Window trait extension directly through Rust: 
```rust
use tauri_plugin_positioner::{WindowExt, Position};


let mut win = app.get_webview_window("main").unwrap();
let _ = win.as_ref().window().move_window(Position::TopRight);
```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    ...,
    +"positioner:default",
  ]
}
```
 ## [Default Permission](#default-permission) Allows the moveWindow and handleIconState APIs #### This default permission set includes the following: * `allow-move-window` * `allow-move-window-constrained` * `allow-set-tray-icon-state` ## Permission Table | Identifier | Description | | ------------------------------------------ | ----------------------------------------------------------------------------- | | `positioner:allow-move-window` | Enables the move_window command without any pre-configured scope. | | `positioner:deny-move-window` | Denies the move_window command without any pre-configured scope. | | `positioner:allow-move-window-constrained` | Enables the move_window_constrained command without any pre-configured scope. | | `positioner:deny-move-window-constrained` | Denies the move_window_constrained command without any pre-configured scope. | | `positioner:allow-set-tray-icon-state` | Enables the set_tray_icon_state command without any pre-configured scope. | | `positioner:deny-set-tray-icon-state` | Denies the set_tray_icon_state command without any pre-configured scope. |

# Process

> Access the current process.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/process)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-process)[crates.io](https://crates.io/crates/tauri-plugin-process) API Reference:[](/reference/javascript/process/)[](https://docs.rs/tauri-plugin-process) This plugin provides APIs to access the current process. To spawn child processes, see the [shell](/plugin/shell/) plugin. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the plugin-process to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add process
    ```
 * yarn 
    ```sh
    yarn run tauri add process
    ```
 * pnpm 
    ```sh
    pnpm tauri add process
    ```
 * deno 
    ```sh
    deno task tauri add process
    ```
 * bun 
    ```sh
    bun tauri add process
    ```
 * cargo 
    ```sh
    cargo tauri add process
    ```
 * Manual 
  ```sh
  npm run tauri add process
  ```
 * npm 
  ```sh
  yarn run tauri add process
  ```
 * yarn 
  ```sh
  pnpm tauri add process
  ```
 * pnpm 
  ```sh
  deno task tauri add process
  ```
 * deno 
  ```sh
  bun tauri add process
  ```
 * bun 
  ```sh
  cargo tauri add process
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-process
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_process::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. If you’d like to utilize the plugin in JavaScript then install the npm package as well: * npm 
       ```sh
       npm install @tauri-apps/plugin-process
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-process
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-process
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-process
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-process
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-process
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-process
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-process
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-process
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-process
  ```
 ## Usage The process plugin is available in both JavaScript and Rust. * JavaScript 
  ```javascript
  import { exit, relaunch } from '@tauri-apps/plugin-process';
  // when using `"withGlobalTauri": true`, you may use
  // const { exit, relaunch } = window.__TAURI__.process;


  // exits the app with the given status code
  await exit(0);


  // restarts the app
  await relaunch();
  ```
 * Rust Note that `app` is an instance of [`AppHandle`](https://docs.rs/tauri/2.0.0/tauri/struct.AppHandle.html). 
  ```rust
  // exits the app with the given status code
  app.exit(0);


  // restarts the app
  app.restart();
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    ...,
    +"process:default",
  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures which process features are by default exposed. #### [Granted Permissions](#granted-permissions) This enables to quit via `allow-exit` and restart via `allow-restart` the application. #### This default permission set includes the following: * `allow-exit` * `allow-restart` ## Permission Table | Identifier | Description | | ----------------------- | ------------------------------------------------------------- | | `process:allow-exit` | Enables the exit command without any pre-configured scope. | | `process:deny-exit` | Denies the exit command without any pre-configured scope. | | `process:allow-restart` | Enables the restart command without any pre-configured scope. | | `process:deny-restart` | Denies the restart command without any pre-configured scope. |

# Shell

> Access the system shell to spawn child processes.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/shell)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-shell)[crates.io](https://crates.io/crates/tauri-plugin-shell) API Reference:[](/reference/javascript/shell/)[](https://docs.rs/tauri-plugin-shell) Access the system shell. Allows you to spawn child processes. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----------------------------------- | | windows | | | | linux | | | | macos | | | | android | | Only allows to open URLs via `open` | | ios | | Only allows to open URLs via `open` | ## Opener If you’re looking for documentation for the `shell.open` API, check out the new [Opener plugin](../opener/) instead. ## Setup Install the shell plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add shell
    ```
 * yarn 
    ```sh
    yarn run tauri add shell
    ```
 * pnpm 
    ```sh
    pnpm tauri add shell
    ```
 * deno 
    ```sh
    deno task tauri add shell
    ```
 * bun 
    ```sh
    bun tauri add shell
    ```
 * cargo 
    ```sh
    cargo tauri add shell
    ```
 * Manual 
  ```sh
  npm run tauri add shell
  ```
 * npm 
  ```sh
  yarn run tauri add shell
  ```
 * yarn 
  ```sh
  pnpm tauri add shell
  ```
 * pnpm 
  ```sh
  deno task tauri add shell
  ```
 * deno 
  ```sh
  bun tauri add shell
  ```
 * bun 
  ```sh
  cargo tauri add shell
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-shell
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_shell::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-shell
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-shell
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-shell
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-shell
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-shell
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-shell
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-shell
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-shell
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-shell
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-shell
  ```
 ## Usage The shell plugin is available in both JavaScript and Rust. * JavaScript 
  ```javascript
  import { Command } from '@tauri-apps/plugin-shell';
  // when using `"withGlobalTauri": true`, you may use
  // const { Command } = window.__TAURI__.shell;


  let result = await Command.create('exec-sh', [
    '-c',
    "echo 'Hello World!'",
  ]).execute();
  console.log(result);
  ```
 * Rust 
  ```rust
  use tauri_plugin_shell::ShellExt;


  let shell = app_handle.shell();
  let output = tauri::async_runtime::block_on(async move {
      shell
          .command("echo")
          .args(["Hello from Rust!"])
          .output()
          .await
          .unwrap()
  });
  if output.status.success() {
      println!("Result: {:?}", String::from_utf8(output.stdout));
  } else {
      println!("Exit with code: {}", output.status.code().unwrap());
  }
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  +"permissions": [
+    {
      +"identifier": "shell:allow-execute",
      +"allow": [
+        {
          +"name": "exec-sh",
          +"cmd": "sh",
          +"args": [
            +"-c",
+            {
              +"validator": "\\S+"
+            }
+          ],
          +"sidecar": false
+        }
+      ]
+    }
+  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures which shell functionality is exposed by default. #### [Granted Permissions](#granted-permissions) It allows to use the `open` functionality with a reasonable scope pre-configured. It will allow opening `http(s)://`, `tel:` and `mailto:` links. #### This default permission set includes the following: * `allow-open` ## Permission Table | Identifier | Description | | ------------------------- | ----------------------------------------------------------------- | | `shell:allow-execute` | Enables the execute command without any pre-configured scope. | | `shell:deny-execute` | Denies the execute command without any pre-configured scope. | | `shell:allow-kill` | Enables the kill command without any pre-configured scope. | | `shell:deny-kill` | Denies the kill command without any pre-configured scope. | | `shell:allow-open` | Enables the open command without any pre-configured scope. | | `shell:deny-open` | Denies the open command without any pre-configured scope. | | `shell:allow-spawn` | Enables the spawn command without any pre-configured scope. | | `shell:deny-spawn` | Denies the spawn command without any pre-configured scope. | | `shell:allow-stdin-write` | Enables the stdin_write command without any pre-configured scope. | | `shell:deny-stdin-write` | Denies the stdin_write command without any pre-configured scope. |

# Single Instance

> Ensure that a single instance of your Tauri app is running at a time.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/single-instance)[crates.io](https://crates.io/crates/tauri-plugin-single-instance) API Reference:[](https://docs.rs/tauri-plugin-single-instance) Ensure that a single instance of your tauri app is running at a time using the Single Instance Plugin. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the Single Instance plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add single-instance
    ```
 * yarn 
    ```sh
    yarn run tauri add single-instance
    ```
 * pnpm 
    ```sh
    pnpm tauri add single-instance
    ```
 * deno 
    ```sh
    deno task tauri add single-instance
    ```
 * bun 
    ```sh
    bun tauri add single-instance
    ```
 * cargo 
    ```sh
    cargo tauri add single-instance
    ```
 * Manual 
  ```sh
  npm run tauri add single-instance
  ```
 * npm 
  ```sh
  yarn run tauri add single-instance
  ```
 * yarn 
  ```sh
  pnpm tauri add single-instance
  ```
 * pnpm 
  ```sh
  deno task tauri add single-instance
  ```
 * deno 
  ```sh
  bun tauri add single-instance
  ```
 * bun 
  ```sh
  cargo tauri add single-instance
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-single-instance --target 'cfg(any(target_os = "macos", windows, target_os = "linux"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(desktop)]
                 +app.handle().plugin(tauri_plugin_single_instance::init(|app, args, cwd| {}));
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 Note The Single Instance plugin must be the first one to be registered to work well. This assures that it runs before other plugins can interfere. ## Usage The plugin is already installed and initialized, and it should be functioning correctly right away. Nevertheless, we can also enhance its functionality with the `init()` method. The plugin `init()` method takes a closure that is invoked when a new app instance was started, but closed by the plugin. The closure has three arguments: 1. **`app`:** The [AppHandle](https://docs.rs/tauri/2.0.0/tauri/struct.AppHandle.html) of the application. 2. **`args`:** The list of arguments, that was passed by the user to initiate this new instance. 3. **`cwd`:** The Current Working Directory denotes the directory from which the new application instance was launched. So, the closure should look like below 
```rust
.plugin(tauri_plugin_single_instance::init(|app, args, cwd| {
  // Write your code here...
}))
```
 ### Focusing on New Instance By default, when you initiate a new instance while the application is already running, no action is taken. To focus the window of the running instance when user tries to open a new instance, alter the callback closure as follows: src-tauri/src/lib.rs 
```rust
use tauri::{AppHandle, Manager};


pub fn run() {
    let mut builder = tauri::Builder::default();
    #[cfg(desktop)]
    {
        builder = builder.plugin(tauri_plugin_single_instance::init(|app, args, cwd| {
            let _ = app.get_webview_window("main")
                       .expect("no main window")
                       .set_focus();
        }));
    }


    builder
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```
 ## Usage in Snap and Flatpak On Linux the Single Instance plugin uses DBus to ensure that there will be only one instance running. It does so by publishing a service to DBus when the first instance starts running. Then, the following instances will try to publish the same service and, if it is already published, they will send a request to the service to notify the first instance, and exit right away. Despite this working pretty well when your app is bundled as a deb or rpm package or an AppImage, it won’t work as intended for snap or flatpak packages by default because these packages run in a constrained sandboxed environment, where most of the communication to DBus services will be blocked if not explicitly declared on the packaging manifest. Here’s a guide that shows how to declare the needed permissions to enable the Single Instance for snap and flatpak packages: ### Getting your app ID The Single Instance plugin will publish a service named `org.{id}.SingleInstance`. `{id}` will be the `identifier` from your `tauri.conf.json` file, but with dots (`.`) and dashes (`-`) replaced by underline (`_`). For example, if your identifier is `net.mydomain.MyApp`: * `net_mydomain_MyApp` will be your app `{id}` * `org.net_mydomain_MyApp.SingleInstance` will be your app SingleInstance service name You will need the service name to authorize your app to use the DBus service on snap and flatpak manifests, as seen below. ### Snap In your snapcraft.yml file, declare a plug and a slot for the single instance service, and use both on your app declaration: snapcraft.yml 
```yaml
# ...
slots:
  single-instance:
    interface: dbus
    bus: session
    name: org.net_mydomain_MyApp.SingleInstance # Remember to change net_mydomain_MyApp to your app ID


plugs:
  single-instance-plug:
    interface: dbus
    bus: session
    name: org.net_mydomain_MyApp.SingleInstance # Remember to change net_mydomain_MyApp to your app ID


# .....
apps:
  my-app:
    # ...
    plugs:
      # ....
      - single-instance-plug
    slots:
      # ...
      - single-instance


    # ....
```
 This will allow your app to send and receive requests from/to the DBus service as expected by the Single Instance plugin. ### Flatpak In your flatpak manifest file (your.app.id.yml or your.app.id.json), declare a `--talk-name` and a `--own-name` finish args with the service name: net.mydomain.MyApp.yml 
```yaml
# ...
finish-args:
  - --socket=wayland
  - --socket=fallback-x11
  - --device=dri
  - --share=ipc
  # ....
  - --talk-name=org.net_mydomain_MyApp.SingleInstance # Remember to change net_mydomain_MyApp to your app ID
  - --own-name=org.net_mydomain_MyApp.SingleInstance # Remember to change net_mydomain_MyApp to your app ID
# ...
```
 This will allow your app to send and receive requests from/to the DBus service as expected by the Single Instance plugin. ## Permissions Because this Plugin currently does not have JavaScript APIs you do not have to configure [capabilities](/security/capabilities/) to use it.

# SQL

> Tauri Plugin providing an interface for the frontend to communicate with SQL databases through sqlx.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/sql)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-sql)[crates.io](https://crates.io/crates/tauri-plugin-sql) API Reference:[](/reference/javascript/sql/)[](https://docs.rs/tauri-plugin-sql) Plugin providing an interface for the frontend to communicate with SQL databases through [sqlx](https://github.com/launchbadge/sqlx). It supports the SQLite, MySQL and PostgreSQL drivers, enabled by a Cargo feature. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the SQL plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add sql
    ```
 * yarn 
    ```sh
    yarn run tauri add sql
    ```
 * pnpm 
    ```sh
    pnpm tauri add sql
    ```
 * deno 
    ```sh
    deno task tauri add sql
    ```
 * bun 
    ```sh
    bun tauri add sql
    ```
 * cargo 
    ```sh
    cargo tauri add sql
    ```
 * Manual 
  ```sh
  npm run tauri add sql
  ```
 * npm 
  ```sh
  yarn run tauri add sql
  ```
 * yarn 
  ```sh
  pnpm tauri add sql
  ```
 * pnpm 
  ```sh
  deno task tauri add sql
  ```
 * deno 
  ```sh
  bun tauri add sql
  ```
 * bun 
  ```sh
  cargo tauri add sql
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-sql
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
         pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_sql::Builder::default().build())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-sql
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-sql
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-sql
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-sql
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-sql
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-sql
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-sql
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-sql
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-sql
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-sql
  ```
 After installing the plugin, you must select the supported database engine. The available engines are Sqlite, MySQL and PostgreSQL. Run the following command in the `src-tauri` folder to enable your preferred engine: * SQLite 
  ```sh
  cargo add tauri-plugin-sql --features sqlite
  ```
 * MySQL 
  ```sh
  cargo add tauri-plugin-sql --features mysql
  ```
 * PostgreSQL 
  ```sh
  cargo add tauri-plugin-sql --features postgres
  ```
 ## Usage All the plugin’s APIs are available through the JavaScript guest bindings: * SQLite The path is relative to [`tauri::api::path::BaseDirectory::AppConfig`](https://docs.rs/tauri/2.0.0/tauri/path/enum.BaseDirectory.html#variant.AppConfig). 
  ```javascript
  import Database from '@tauri-apps/plugin-sql';
  // when using `"withGlobalTauri": true`, you may use
  // const Database = window.__TAURI__.sql;


  const db = await Database.load('sqlite:test.db');
  await db.execute('INSERT INTO ...');
  ```
 * MySQL 
  ```javascript
  import Database from '@tauri-apps/plugin-sql';
  // when using `"withGlobalTauri": true`, you may use
  // const Database = window.__TAURI__.sql;


  const db = await Database.load('mysql://user:password@host/test');
  await db.execute('INSERT INTO ...');
  ```
 * PostgreSQL 
  ```javascript
  import Database from '@tauri-apps/plugin-sql';
  // when using `"withGlobalTauri": true`, you may use
  // const Database = window.__TAURI__.sql;


  const db = await Database.load('postgres://user:password@host/test');
  await db.execute('INSERT INTO ...');
  ```
 ## Syntax We use [sqlx](https://docs.rs/sqlx/latest/sqlx/) as the underlying library and adopt their query syntax. * SQLite Use the “$#” syntax when substituting query data 
  ```javascript
  const result = await db.execute(
    'INSERT into todos (id, title, status) VALUES ($1, $2, $3)',
    [todos.id, todos.title, todos.status]
  );


  const result = await db.execute(
    'UPDATE todos SET title = $1, status = $2 WHERE id = $3',
    [todos.title, todos.status, todos.id]
  );
  ```
 * MySQL Use “?” when substituting query data 
  ```javascript
  const result = await db.execute(
    'INSERT into todos (id, title, status) VALUES (?, ?, ?)',
    [todos.id, todos.title, todos.status]
  );


  const result = await db.execute(
    'UPDATE todos SET title = ?, status = ? WHERE id = ?',
    [todos.title, todos.status, todos.id]
  );
  ```
 * PostgreSQL Use the “$#” syntax when substituting query data 
  ```javascript
  const result = await db.execute(
    'INSERT into todos (id, title, status) VALUES ($1, $2, $3)',
    [todos.id, todos.title, todos.status]
  );


  const result = await db.execute(
    'UPDATE todos SET title = $1, status = $2 WHERE id = $3',
    [todos.title, todos.status, todos.id]
  );
  ```
 ## Migrations This plugin supports database migrations, allowing you to manage database schema evolution over time. ### Defining Migrations Migrations are defined in Rust using the [`Migration`](https://docs.rs/tauri-plugin-sql/latest/tauri_plugin_sql/struct.Migration.html) struct. Each migration should include a unique version number, a description, the SQL to be executed, and the type of migration (Up or Down). Example of a migration: 
```rust
use tauri_plugin_sql::{Migration, MigrationKind};


let migration = Migration {
    version: 1,
    description: "create_initial_tables",
    sql: "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);",
    kind: MigrationKind::Up,
};
```
 Or if you want to use SQL from a file, you can include it by using `include_str!`: 
```rust
use tauri_plugin_sql::{Migration, MigrationKind};


let migration = Migration {
    version: 1,
    description: "create_initial_tables",
    sql: include_str!("../drizzle/0000_graceful_boomer.sql"),
    kind: MigrationKind::Up,
};
```
 ### Adding Migrations to the Plugin Builder Migrations are registered with the [`Builder`](https://docs.rs/tauri-plugin-sql/latest/tauri_plugin_sql/struct.Builder.html) struct provided by the plugin. Use the `add_migrations` method to add your migrations to the plugin for a specific database connection. Example of adding migrations: src-tauri/src/main.rs 
```rust
use tauri_plugin_sql::{Builder, Migration, MigrationKind};


fn main() {
    let migrations = vec![
        // Define your migrations here
        Migration {
            version: 1,
            description: "create_initial_tables",
            sql: "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);",
            kind: MigrationKind::Up,
        }
    ];


    tauri::Builder::default()
        .plugin(
            tauri_plugin_sql::Builder::default()
                .add_migrations("sqlite:mydatabase.db", migrations)
                .build(),
        )
        ...
}
```
 ### Applying Migrations To apply the migrations when the plugin is initialized, add the connection string to the `tauri.conf.json` file: src-tauri/tauri.conf.json 
```json
{
  "plugins": {
    "sql": {
      "preload": ["sqlite:mydatabase.db"]
    }
  }
}
```
 Alternatively, the client side `load()` also runs the migrations for a given connection string: 
```ts
import Database from '@tauri-apps/plugin-sql';
const db = await Database.load('sqlite:mydatabase.db');
```
 Ensure that the migrations are defined in the correct order and are safe to run multiple times. Note All migrations are executed within a transaction, ensuring atomicity. If any migration fails, the entire transaction is rolled back, leaving the database in a consistent state. ### Migration Management * **Version Control**: Each migration must have a unique version number. This is crucial for ensuring the migrations are applied in the correct order. * **Idempotency**: Write migrations in a way that they can be safely re-run without causing errors or unintended consequences. * **Testing**: Thoroughly test migrations to ensure they work as expected and do not compromise the integrity of your database. ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    ...,
    +"sql:default",
    +"sql:allow-execute",
  ]
}
```
 ## [Default Permission](#default-permission) ### [Default Permissions](#default-permissions) This permission set configures what kind of database operations are available from the sql plugin. ### Granted Permissions All reading related operations are enabled. Also allows to load or close a connection. #### This default permission set includes the following: * `allow-close` * `allow-load` * `allow-select` ## Permission Table | Identifier | Description | | ------------------- | ------------------------------------------------------------- | | `sql:allow-close` | Enables the close command without any pre-configured scope. | | `sql:deny-close` | Denies the close command without any pre-configured scope. | | `sql:allow-execute` | Enables the execute command without any pre-configured scope. | | `sql:deny-execute` | Denies the execute command without any pre-configured scope. | | `sql:allow-load` | Enables the load command without any pre-configured scope. | | `sql:deny-load` | Denies the load command without any pre-configured scope. | | `sql:allow-select` | Enables the select command without any pre-configured scope. | | `sql:deny-select` | Denies the select command without any pre-configured scope. |

# Store

> Persistent key value storage.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/store)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-store)[crates.io](https://crates.io/crates/tauri-plugin-store) API Reference:[](/reference/javascript/store/)[](https://docs.rs/tauri-plugin-store) This plugin provides a persistent key-value store. This is one of many options to handle state in your application. See the [state management overview](/develop/state-management/) for more information on additional options. This store will allow you to persist state to a file which can be saved and loaded on demand including between app restarts. Note that this process is asynchronous which will require handling it within your code. It can be used both in the webview or within Rust. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the store plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add store
    ```
 * yarn 
    ```sh
    yarn run tauri add store
    ```
 * pnpm 
    ```sh
    pnpm tauri add store
    ```
 * deno 
    ```sh
    deno task tauri add store
    ```
 * bun 
    ```sh
    bun tauri add store
    ```
 * cargo 
    ```sh
    cargo tauri add store
    ```
 * Manual 
  ```sh
  npm run tauri add store
  ```
 * npm 
  ```sh
  yarn run tauri add store
  ```
 * yarn 
  ```sh
  pnpm tauri add store
  ```
 * pnpm 
  ```sh
  deno task tauri add store
  ```
 * deno 
  ```sh
  bun tauri add store
  ```
 * bun 
  ```sh
  cargo tauri add store
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-store
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_store::Builder::new().build())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-store
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-store
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-store
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-store
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-store
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-store
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-store
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-store
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-store
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-store
  ```
 ## Usage * JavaScript 
  ```typescript
  import { load } from '@tauri-apps/plugin-store';
  // when using `"withGlobalTauri": true`, you may use
  // const { load } = window.__TAURI__.store;


  // Create a new store or load the existing one,
  // note that the options will be ignored if a `Store` with that path has already been created
  const store = await load('store.json', { autoSave: false });


  // Set a value.
  await store.set('some-key', { value: 5 });


  // Get a value.
  const val = await store.get<{ value: number }>('some-key');
  console.log(val); // { value: 5 }


  // You can manually save the store after making changes.
  // Otherwise, it will save upon graceful exit
  // And if you set `autoSave` to a number or left empty,
  // it will save the changes to disk after a debounce delay, 100ms by default.
  await store.save();
  ```
 * Rust src-tauri/src/lib.rs 
  ```rust
  use tauri::Wry;
  use tauri_plugin_store::StoreExt;
  use serde_json::json;


  #[cfg_attr(mobile, tauri::mobile_entry_point)]
  pub fn run() {
      tauri::Builder::default()
          .plugin(tauri_plugin_store::Builder::default().build())
          .setup(|app| {
              // Create a new store or load the existing one
              // this also put the store in the app's resource table
              // so your following `store` calls (from both Rust and JS)
              // will reuse the same store.


              let store = app.store("store.json")?;


              // Note that values must be serde_json::Value instances,
              // otherwise, they will not be compatible with the JavaScript bindings.
              store.set("some-key", json!({ "value": 5 }));


              // Get a value from the store.
              let value = store.get("some-key").expect("Failed to get value from store");
              println!("{}", value); // {"value":5}


              // Remove the store from the resource table
              store.close_resource();


              Ok(())
          })
          .run(tauri::generate_context!())
          .expect("error while running tauri application");
  }
  ```
 ### LazyStore There’s also a high level JavaScript API `LazyStore` which only loads the store on first access 
```typescript
import { LazyStore } from '@tauri-apps/plugin-store';


const store = new LazyStore('settings.json');
```
 ## Migrating from v1 and v2 beta/rc * JavaScript 
  ```diff
  import { Store } from '@tauri-apps/plugin-store';
  import { LazyStore } from '@tauri-apps/plugin-store';
  ```
 * Rust 
  ```diff
  with_store(app.handle().clone(), stores, path, |store| {
      store.insert("some-key".to_string(), json!({ "value": 5 }))?;
      Ok(())
  });
  let store = app.store(path)?;
  store.set("some-key".to_string(), json!({ "value": 5 }));
  ```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    ...,
    +"store:default",
  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures what kind of operations are available from the store plugin. #### [Granted Permissions](#granted-permissions) All operations are enabled by default. #### This default permission set includes the following: * `allow-load` * `allow-get-store` * `allow-set` * `allow-get` * `allow-has` * `allow-delete` * `allow-clear` * `allow-reset` * `allow-keys` * `allow-values` * `allow-entries` * `allow-length` * `allow-reload` * `allow-save` ## Permission Table | Identifier | Description | | ----------------------- | --------------------------------------------------------------- | | `store:allow-clear` | Enables the clear command without any pre-configured scope. | | `store:deny-clear` | Denies the clear command without any pre-configured scope. | | `store:allow-delete` | Enables the delete command without any pre-configured scope. | | `store:deny-delete` | Denies the delete command without any pre-configured scope. | | `store:allow-entries` | Enables the entries command without any pre-configured scope. | | `store:deny-entries` | Denies the entries command without any pre-configured scope. | | `store:allow-get` | Enables the get command without any pre-configured scope. | | `store:deny-get` | Denies the get command without any pre-configured scope. | | `store:allow-get-store` | Enables the get_store command without any pre-configured scope. | | `store:deny-get-store` | Denies the get_store command without any pre-configured scope. | | `store:allow-has` | Enables the has command without any pre-configured scope. | | `store:deny-has` | Denies the has command without any pre-configured scope. | | `store:allow-keys` | Enables the keys command without any pre-configured scope. | | `store:deny-keys` | Denies the keys command without any pre-configured scope. | | `store:allow-length` | Enables the length command without any pre-configured scope. | | `store:deny-length` | Denies the length command without any pre-configured scope. | | `store:allow-load` | Enables the load command without any pre-configured scope. | | `store:deny-load` | Denies the load command without any pre-configured scope. | | `store:allow-reload` | Enables the reload command without any pre-configured scope. | | `store:deny-reload` | Denies the reload command without any pre-configured scope. | | `store:allow-reset` | Enables the reset command without any pre-configured scope. | | `store:deny-reset` | Denies the reset command without any pre-configured scope. | | `store:allow-save` | Enables the save command without any pre-configured scope. | | `store:deny-save` | Denies the save command without any pre-configured scope. | | `store:allow-set` | Enables the set command without any pre-configured scope. | | `store:deny-set` | Denies the set command without any pre-configured scope. | | `store:allow-values` | Enables the values command without any pre-configured scope. | | `store:deny-values` | Denies the values command without any pre-configured scope. |

# Stronghold

> Encrypted, secure database.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/stronghold)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-stronghold)[crates.io](https://crates.io/crates/tauri-plugin-stronghold) API Reference:[](/reference/javascript/stronghold/)[](https://docs.rs/tauri-plugin-stronghold) Store secrets and keys using the [IOTA Stronghold](https://github.com/iotaledger/stronghold.rs) secret management engine. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the stronghold plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add stronghold
    ```
 * yarn 
    ```sh
    yarn run tauri add stronghold
    ```
 * pnpm 
    ```sh
    pnpm tauri add stronghold
    ```
 * deno 
    ```sh
    deno task tauri add stronghold
    ```
 * bun 
    ```sh
    bun tauri add stronghold
    ```
 * cargo 
    ```sh
    cargo tauri add stronghold
    ```
 * Manual 
  ```sh
  npm run tauri add stronghold
  ```
 * npm 
  ```sh
  yarn run tauri add stronghold
  ```
 * yarn 
  ```sh
  pnpm tauri add stronghold
  ```
 * pnpm 
  ```sh
  deno task tauri add stronghold
  ```
 * deno 
  ```sh
  bun tauri add stronghold
  ```
 * bun 
  ```sh
  cargo tauri add stronghold
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-stronghold
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_stronghold::Builder::new(|password| {}).build())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-stronghold
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-stronghold
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-stronghold
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-stronghold
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-stronghold
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-stronghold
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-stronghold
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-stronghold
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-stronghold
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-stronghold
  ```
 Due to an [upstream bug](https://github.com/tauri-apps/plugins-workspace/issues/2048) we also recommend that you add this to your `Cargo.toml` file: 
```toml
[profile.dev.package.scrypt]
opt-level = 3
```
 ## Usage The plugin must be initialized with a password hash function, which takes the password string and must return a 32 bytes hash derived from it. ### Initialize with argon2 password hash function The Stronghold plugin offers a default hash function using the [argon2](https://docs.rs/rust-argon2/latest/argon2/) algorithm. src-tauri/src/lib.rs 
```rust
use tauri::Manager;


pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let salt_path = app
                .path()
                .app_local_data_dir()
                .expect("could not resolve app local data path")
                .join("salt.txt");
            app.handle().plugin(tauri_plugin_stronghold::Builder::with_argon2(&salt_path).build())?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```
 ### Initialize with custom password hash function Alternatively you can provide your own hash algorithm by using the `tauri_plugin_stronghold::Builder::new` constructor. Note The password hash must contain exactly 32 bytes. This is a Stronghold requirement. src-tauri/src/lib.rs 
```rust
pub fn run() {
    tauri::Builder::default()
        .plugin(
            tauri_plugin_stronghold::Builder::new(|password| {
                // Hash the password here with e.g. argon2, blake2b or any other secure algorithm
                // Here is an example implementation using the `rust-argon2` crate for hashing the password
                use argon2::{hash_raw, Config, Variant, Version};


                let config = Config {
                    lanes: 4,
                    mem_cost: 10_000,
                    time_cost: 10,
                    variant: Variant::Argon2id,
                    version: Version::Version13,
                    ..Default::default()
                };
                let salt = "your-salt".as_bytes();
                let key = hash_raw(password.as_ref(), salt, &config).expect("failed to hash password");


                key.to_vec()
            })
            .build(),
        )
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```
 ### Usage from JavaScript The stronghold plugin is available in JavaScript. 
```javascript
import { Client, Stronghold } from '@tauri-apps/plugin-stronghold';
// when using `"withGlobalTauri": true`, you may use
// const { Client, Stronghold } = window.__TAURI__.stronghold;
import { appDataDir } from '@tauri-apps/api/path';
// when using `"withGlobalTauri": true`, you may use
// const { appDataDir } = window.__TAURI__.path;


const initStronghold = async () => {
  const vaultPath = `${await appDataDir()}/vault.hold`;
  const vaultPassword = 'vault password';
  const stronghold = await Stronghold.load(vaultPath, vaultPassword);


  let client: Client;
  const clientName = 'name your client';
  try {
    client = await stronghold.loadClient(clientName);
  } catch {
    client = await stronghold.createClient(clientName);
  }


  return {
    stronghold,
    client,
  };
};


// Insert a record to the store
async function insertRecord(store: any, key: string, value: string) {
  const data = Array.from(new TextEncoder().encode(value));
  await store.insert(key, data);
}


// Read a record from store
async function getRecord(store: any, key: string): Promise<string> {
  const data = await store.get(key);
  return new TextDecoder().decode(new Uint8Array(data));
}


const { stronghold, client } = await initStronghold();


const store = client.getStore();
const key = 'my_key';


// Insert a record to the store
insertRecord(store, key, 'secret value');


// Read a record from store
const value = await getRecord(store, key);
console.log(value); // 'secret value'


// Save your updates
await stronghold.save();


// Remove a record from store
await store.remove(key);
```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  ...,
  "permissions": [
    +"stronghold:default",
  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures what kind of operations are available from the stronghold plugin. #### [Granted Permissions](#granted-permissions) All non-destructive operations are enabled by default. #### This default permission set includes the following: * `allow-create-client` * `allow-get-store-record` * `allow-initialize` * `allow-execute-procedure` * `allow-load-client` * `allow-save-secret` * `allow-save-store-record` * `allow-save` ## Permission Table | Identifier | Description | | -------------------------------------- | ------------------------------------------------------------------------- | | `stronghold:allow-create-client` | Enables the create_client command without any pre-configured scope. | | `stronghold:deny-create-client` | Denies the create_client command without any pre-configured scope. | | `stronghold:allow-destroy` | Enables the destroy command without any pre-configured scope. | | `stronghold:deny-destroy` | Denies the destroy command without any pre-configured scope. | | `stronghold:allow-execute-procedure` | Enables the execute_procedure command without any pre-configured scope. | | `stronghold:deny-execute-procedure` | Denies the execute_procedure command without any pre-configured scope. | | `stronghold:allow-get-store-record` | Enables the get_store_record command without any pre-configured scope. | | `stronghold:deny-get-store-record` | Denies the get_store_record command without any pre-configured scope. | | `stronghold:allow-initialize` | Enables the initialize command without any pre-configured scope. | | `stronghold:deny-initialize` | Denies the initialize command without any pre-configured scope. | | `stronghold:allow-load-client` | Enables the load_client command without any pre-configured scope. | | `stronghold:deny-load-client` | Denies the load_client command without any pre-configured scope. | | `stronghold:allow-remove-secret` | Enables the remove_secret command without any pre-configured scope. | | `stronghold:deny-remove-secret` | Denies the remove_secret command without any pre-configured scope. | | `stronghold:allow-remove-store-record` | Enables the remove_store_record command without any pre-configured scope. | | `stronghold:deny-remove-store-record` | Denies the remove_store_record command without any pre-configured scope. | | `stronghold:allow-save` | Enables the save command without any pre-configured scope. | | `stronghold:deny-save` | Denies the save command without any pre-configured scope. | | `stronghold:allow-save-secret` | Enables the save_secret command without any pre-configured scope. | | `stronghold:deny-save-secret` | Denies the save_secret command without any pre-configured scope. | | `stronghold:allow-save-store-record` | Enables the save_store_record command without any pre-configured scope. | | `stronghold:deny-save-store-record` | Denies the save_store_record command without any pre-configured scope. |

# Updater

> In-app updates for Tauri applications.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/updater)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-updater)[crates.io](https://crates.io/crates/tauri-plugin-updater) API Reference:[](/reference/javascript/updater/)[](https://docs.rs/tauri-plugin-updater) Automatically update your Tauri app with an update server or a static JSON. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the Tauri updater plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add updater
    ```
 * yarn 
    ```sh
    yarn run tauri add updater
    ```
 * pnpm 
    ```sh
    pnpm tauri add updater
    ```
 * deno 
    ```sh
    deno task tauri add updater
    ```
 * bun 
    ```sh
    bun tauri add updater
    ```
 * cargo 
    ```sh
    cargo tauri add updater
    ```
 * Manual 
  ```sh
  npm run tauri add updater
  ```
 * npm 
  ```sh
  yarn run tauri add updater
  ```
 * yarn 
  ```sh
  pnpm tauri add updater
  ```
 * pnpm 
  ```sh
  deno task tauri add updater
  ```
 * deno 
  ```sh
  bun tauri add updater
  ```
 * bun 
  ```sh
  cargo tauri add updater
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-updater --target 'cfg(any(target_os = "macos", windows, target_os = "linux"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             .setup(|app| {
     +            #[cfg(desktop)]
                 +app.handle().plugin(tauri_plugin_updater::Builder::new().build());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. You can install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-updater
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-updater
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-updater
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-updater
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-updater
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-updater
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-updater
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-updater
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-updater
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-updater
  ```
 ## Signing updates Tauri’s updater needs a signature to verify that the update is from a trusted source. This cannot be disabled. To sign your updates you need two keys: 1. The public key, which will be set in the `tauri.conf.json` to validate the artifacts before the installation. This public key can be uploaded and shared safely as long as your private key is secure. 2. The private key, which is used to sign your installer files. You should NEVER share this key with anyone. Also, if you lose this key you will NOT be able to publish new updates to the users that have the app already installed. It is important to store this key in a safe place! To generate the keys the Tauri CLI provides the `signer generate` command. You can run this to create the keys in the home folder: * npm 
  ```sh
  npm run tauri signer generate -- -w ~/.tauri/myapp.key
  ```
 * yarn 
  ```sh
  yarn tauri signer generate -w ~/.tauri/myapp.key
  ```
 * pnpm 
  ```sh
  pnpm tauri signer generate -w ~/.tauri/myapp.key
  ```
 * deno 
  ```sh
  deno task tauri signer generate -w ~/.tauri/myapp.key
  ```
 * bun 
  ```sh
  bunx tauri signer generate -w ~/.tauri/myapp.key
  ```
 * cargo 
  ```sh
  cargo tauri signer generate -w ~/.tauri/myapp.key
  ```
 ### Building While building your update artifacts, you need to have the private key you generated above in your environment variables. `.env` files do *not* work! * Mac/Linux 
  ```sh
  export TAURI_SIGNING_PRIVATE_KEY="Path or content of your private key"
  # optionally also add a password
  export TAURI_SIGNING_PRIVATE_KEY_PASSWORD=""
  ```
 * Windows Run this in `PowerShell`: 
  ```ps
  $env:TAURI_SIGNING_PRIVATE_KEY="Path or content of your private key"
  <# optionally also add a password #>
  $env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD=""
  ```
 After that, you can run Tauri build as usual and Tauri will generate the update bundles and their signatures. The generated files depend on the [`createUpdaterArtifacts`](/reference/config/#createupdaterartifacts) configuration value configured below. * v2 
  ```json
  {
    "bundle": {
      "createUpdaterArtifacts": true
    }
  }
  ```
 On Linux, Tauri will create the normal AppImage inside the `target/release/bundle/appimage/` folder: * `myapp.AppImage` - The standard app bundle. It will be re-used by the updater. * `myapp.AppImage.sig` - The signature of the updater bundle. On macOS, Tauri will create a .tar.gz archive from the application bundle inside the target/release/bundle/macos/ folder: * `myapp.app` - The standard app bundle. * `myapp.app.tar.gz` - The updater bundle. * `myapp.app.tar.gz.sig` - The signature of the update bundle. On Windows, Tauri will create the normal MSI and NSIS installers inside the target/release/bundle/msi/ and target/release/bundle/nsis folders: * `myapp-setup.exe` - The standard app bundle. It will be re-used by the updater. * `myapp-setup.exe.sig` - The signature of the update bundle. * `myapp.msi` - The standard app bundle. It will be re-used by the updater. * `myapp.msi.sig` - The signature of the update bundle. * v1 compatible 
  ```json
  {
    "bundle": {
      "createUpdaterArtifacts": "v1Compatible"
    }
  }
  ```
 On Linux, Tauri will create a .tar.gz archive from the AppImage inside the `target/release/bundle/appimage/` folder: * `myapp.AppImage` - The standard app bundle. * `myapp.AppImage.tar.gz` - The updater bundle. * `myapp.AppImage.tar.gz.sig` - The signature of the update bundle. On macOS, Tauri will create a .tar.gz archive from the application bundle inside the target/release/bundle/macos/ folder: * `myapp.app` - The standard app bundle. * `myapp.app.tar.gz` - The updater bundle. * `myapp.app.tar.gz.sig` - The signature of the update bundle. On Windows, Tauri will create .zip archives from the MSI and NSIS installers inside the target/release/bundle/msi/ and target/release/bundle/nsis folders: * `myapp-setup.exe` - The standard app bundle. * `myapp-setup.nsis.zip` - The updater bundle. * `myapp-setup.nsis.zip.sig` - The signature of the update bundle. * `myapp.msi` - The standard app bundle. * `myapp.msi.zip` - The updater bundle. * `myapp.msi.zip.sig` - The signature of the update bundle. ## Tauri Configuration Set up the `tauri.conf.json` in this format for the updater to start working. | Keys | Description | | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | | `createUpdaterArtifacts` | Setting this to `true` tells Tauri’s app bundler to create updater artifacts. If you’re migrating your app from an older Tauri version, set it to `"v1Compatible"` instead. **This setting will be removed in v3** so make sure to change it to `true` once all your users are migrated to v2. | | `pubkey` | This has to be the public key generated from the Tauri CLI in the step above. It **cannot** be a file path! | | `endpoints` | This must be an array of endpoint URLs as strings. TLS is enforced in production mode. Tauri will only continue to the next url if a non-2XX status code is returned! | | `dangerousInsecureTransportProtocol` | Setting this to `true` allows the updater to accept non-HTTPS endpoints. Use this configuration with caution! | Each updater URL can contain the following dynamic variables, allowing you to determine server-side if an update is available. * `{{current_version}}`: The version of the app that is requesting the update. * `{{target}}`: The operating system name (one of `linux`, `windows` or `darwin`). * `{{arch}}`: The architecture of the machine (one of `x86_64`, `i686`, `aarch64` or `armv7`). tauri.conf.json 
```json
{
  "bundle": {
    "createUpdaterArtifacts": true
  },
  "plugins": {
    "updater": {
      "pubkey": "CONTENT FROM PUBLICKEY.PEM",
      "endpoints": [
        "https://releases.myapp.com/{{target}}/{{arch}}/{{current_version}}",
        // or a static github json file
        "https://github.com/user/repo/releases/latest/download/latest.json"
      ]
    }
  }
}
```
 ### `installMode` on Windows On Windows there is an additional optional `"installMode"` config to change how the update is installed. tauri.conf.json 
```json
{
  "plugins": {
    "updater": {
      "windows": {
        "installMode": "passive"
      }
    }
  }
}
```
 * `"passive"`: There will be a small window with a progress bar. The update will be installed without requiring any user interaction. Generally recommended and the default mode. * `"basicUi"`: There will be a basic user interface shown which requires user interaction to finish the installation. * `"quiet"`: There will be no progress feedback to the user. With this mode the installer cannot request admin privileges by itself so it only works in user-wide installations or when your app itself already runs with admin privileges. Generally not recommended. ## Server Support The updater plugin can be used in two ways. Either with a dynamic update server or a static JSON file (to use on services like S3 or GitHub gists). ### Static JSON File When using static, you just need to return a JSON containing the required information. | Keys | Description | | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | | `version` | Must be a valid [SemVer](https://semver.org/), with or without a leading `v`, meaning that both `1.0.0` and `v1.0.0` are valid. | | `notes` | Notes about the update. | | `pub_date` | The date must be formatted according to [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) if present. | | `platforms` | Each platform key is in the `OS-ARCH` format, where `OS` is one of `linux`, `darwin` or `windows`, and `ARCH` is one of `x86_64`, `aarch64`, `i686` or `armv7`. | | `signature` | The content of the generated `.sig` file, which may change with each build. A path or URL does not work! | Note When using [custom targets](#custom-target) the provided target string is matched against the `platforms` key instead of the default `OS-ARCH` value. The required keys are `"version"`, `"platforms.[target].url"` and `"platforms.[target].signature"`; the others are optional. 
```json
{
  "version": "",
  "notes": "",
  "pub_date": "",
  "platforms": {
    "linux-x86_64": {
      "signature": "",
      "url": ""
    },
    "windows-x86_64": {
      "signature": "",
      "url": ""
    },
    "darwin-x86_64": {
      "signature": "",
      "url": ""
    }
  }
}
```
 Note that Tauri will validate the whole file before checking the version field, so make sure all existing platform configurations are valid and complete. ### Dynamic Update Server When using a dynamic update server, Tauri will follow the server’s instructions. To disable the internal version check you can overwrite the [plugin’s version comparison](https://docs.rs/tauri-plugin-updater/latest/tauri_plugin_updater/struct.UpdaterBuilder.html#method.version_comparator), this will install the version sent by the server (useful if you need to roll back your app). Your server can use variables defined in the `endpoint` URL above to determine if an update is required. If you need more data, you can include additional [request headers in Rust](https://docs.rs/tauri-plugin-updater/latest/tauri_plugin_updater/struct.UpdaterBuilder.html#method.header) to your liking. Your server should respond with a status code of [`204 No Content`](https://datatracker.ietf.org/doc/html/rfc2616#section-10.2.5) if there is no update available. If an update is required, your server should respond with a status code of [`200 OK`](http://tools.ietf.org/html/rfc2616#section-10.2.1) and a JSON response in this format: | Keys | Description | | ----------- | ------------------------------------------------------------------------------------------------------------------------------------ | | `version` | This Must be a valid [SemVer](https://semver.org/), with or without a leading `v`, meaning that both `1.0.0` and `v1.0.0` are valid. | | `notes` | Notes about the update. | | `pub_date` | The date must be formatted according to [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) if present. | | `url` | This Must be a valid URL to the update bundle. | | `signature` | The content of the generated `.sig` file, which may change with each build. A path or URL does not work! | The required keys are `"url"`, `"version"` and `"signature"`; the others are optional. 
```json
{
  "version": "",
  "pub_date": "",
  "url": "",
  "signature": "",
  "notes": ""
}
```
 ## Checking for Updates The default API for checking updates and installing them leverages the configured endpoints and can be accessed by both JavaScript and Rust code. * JavaScript 
  ```js
  import { check } from '@tauri-apps/plugin-updater';
  import { relaunch } from '@tauri-apps/plugin-process';


  const update = await check();
  if (update) {
    console.log(
      `found update ${update.version} from ${update.date} with notes ${update.body}`
    );
    let downloaded = 0;
    let contentLength = 0;
    // alternatively we could also call update.download() and update.install() separately
    await update.downloadAndInstall((event) => {
      switch (event.event) {
        case 'Started':
          contentLength = event.data.contentLength;
          console.log(`started downloading ${event.data.contentLength} bytes`);
          break;
        case 'Progress':
          downloaded += event.data.chunkLength;
          console.log(`downloaded ${downloaded} from ${contentLength}`);
          break;
        case 'Finished':
          console.log('download finished');
          break;
      }
    });


    console.log('update installed');
    await relaunch();
  }
  ```
 For more information see the [JavaScript API documentation](/reference/javascript/updater/). * Rust src-tauri/src/lib.rs 
  ```rust
  use tauri_plugin_updater::UpdaterExt;


  pub fn run() {
    tauri::Builder::default()
      .setup(|app| {
        let handle = app.handle().clone();
        tauri::async_runtime::spawn(async move {
          update(handle).await.unwrap();
        });
        Ok(())
      })
      .run(tauri::generate_context!())
      .unwrap();
  }


  async fn update(app: tauri::AppHandle) -> tauri_plugin_updater::Result<()> {
    if let Some(update) = app.updater()?.check().await? {
      let mut downloaded = 0;


      // alternatively we could also call update.download() and update.install() separately
      update
        .download_and_install(
          |chunk_length, content_length| {
            downloaded += chunk_length;
            println!("downloaded {downloaded} from {content_length:?}");
          },
          || {
            println!("download finished");
          },
        )
        .await?;


      println!("update installed");
      app.restart();
    }


    Ok(())
  }
  ```
 For more information see the [Rust API documentation](https://docs.rs/tauri-plugin-updater). Note that restarting your app immediately after installing an update is not required and you can choose how to handle the update by either waiting until the user manually restarts the app, or prompting them to select when to do so. Note On Windows the application is automatically exited when the install step is executed due to a limitation of Windows installers. When checking and downloading updates it is possible to define a custom request timeout, a proxy and request headers. * JavaScript 
  ```js
  import { check } from '@tauri-apps/plugin-updater';


  const update = await check({
    proxy: '<proxy url>',
    timeout: 30000 /* milliseconds */,
    headers: {
      Authorization: 'Bearer <token>',
    },
  });
  ```
 * Rust 
  ```rust
  use tauri_plugin_updater::UpdaterExt;
  let update = app
    .updater_builder()
    .timeout(std::time::Duration::from_secs(30))
    .proxy("<proxy-url>".parse().expect("invalid URL"))
    .header("Authorization", "Bearer <token>")
    .build()?
    .check()
    .await?;
  ```
 ### Runtime Configuration The updater APIs also allows the updater to be configured at runtime for more flexibility. For security reasons some APIs are only available for Rust. #### Endpoints Setting the URLs that should be requested to check updates at runtime allows more dynamic updates such as separate release channels: 
```rust
use tauri_plugin_updater::UpdaterExt;
let channel = if beta { "beta" } else { "stable" };
let update_url = format!("https://{channel}.myserver.com/{{{{target}}}}-{{{{arch}}}}/{{{{current_version}}}}");


let update = app
  .updater_builder()
  .endpoints(vec![update_url])?
  .build()?
  .check()
  .await?;
```
 #### Public key Setting the public key at runtime can be useful to implement a key rotation logic. It can be set by either the plugin builder or updater builder: 
```rust
tauri_plugin_updater::Builder::new().pubkey("<your public key>").build()
```
 
```rust
use tauri_plugin_updater::UpdaterExt;


let update = app
  .updater_builder()
  .pubkey("<your public key>")
  .build()?
  .check()
  .await?;
```
 #### Custom target By default the updater lets you use the `{{target}}` and `{{arch}}` variables to determine which update asset must be delivered. If you need more information on your updates (e.g. when distributing a Universal macOS binary option or having more build flavors) you can set a custom target. * JavaScript 
  ```js
  import { check } from '@tauri-apps/plugin-updater';


  const update = await check({
    target: 'macos-universal',
  });
  ```
 * Rust Custom targets can be set by either the plugin builder or updater builder: 
  ```rust
  tauri_plugin_updater::Builder::new().target("macos-universal").build()
  ```
 
  ```rust
  use tauri_plugin_updater::UpdaterExt;
  let update = app
    .updater_builder()
    .target("macos-universal")
    .build()?
    .check()
    .await?;
  ```
 Note * When using a custom target it might be easier to use it exclusively to determine the update platform, so you could remove the `{{arch}}` variable. * The value provided as target is the key that is matched against the platform key when using a [Static JSON file](#static-json-file). #### Allowing downgrades By default Tauri checks if the update version is greater than the current app version to verify if it should update or not. To allow downgrades, you must use the updater builder’s `version_comparator` API: 
```rust
use tauri_plugin_updater::UpdaterExt;


let update = app
  .updater_builder()
  .version_comparator(|current, update| {
    // default comparison: `update.version > current`
    update.version != current
  })
  .build()?
  .check()
  .await?;
```
 #### Windows before exit hook Due to a limitation of Windows installers, Tauri will automatically quit your application before installing updates on Windows. To perform an action before that happens, use the `on_before_exit` function: 
```rust
use tauri_plugin_updater::UpdaterExt;


let update = app
  .updater_builder()
  .on_before_exit(|| {
    println!("app is about to exit on Windows!");
  })
  .build()?
  .check()
  .await?;
```
 Note The values from the [configuration](#tauri-configuration) are used as fallback if any of the builder values are not set. ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    ...,
    +"updater:default",
  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures which kind of updater functions are exposed to the frontend. #### [Granted Permissions](#granted-permissions) The full workflow from checking for updates to installing them is enabled. #### This default permission set includes the following: * `allow-check` * `allow-download` * `allow-install` * `allow-download-and-install` ## Permission Table | Identifier | Description | | ------------------------------------ | -------------------------------------------------------------------------- | | `updater:allow-check` | Enables the check command without any pre-configured scope. | | `updater:deny-check` | Denies the check command without any pre-configured scope. | | `updater:allow-download` | Enables the download command without any pre-configured scope. | | `updater:deny-download` | Denies the download command without any pre-configured scope. | | `updater:allow-download-and-install` | Enables the download_and_install command without any pre-configured scope. | | `updater:deny-download-and-install` | Denies the download_and_install command without any pre-configured scope. | | `updater:allow-install` | Enables the install command without any pre-configured scope. | | `updater:deny-install` | Denies the install command without any pre-configured scope. |

# Upload

> File uploads through HTTP.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/upload)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-upload)[crates.io](https://crates.io/crates/tauri-plugin-upload) API Reference:[](/reference/javascript/upload/)[](https://docs.rs/tauri-plugin-upload) Upload files from disk to a remote server over HTTP. Download files from a remote HTTP server to disk. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add upload
    ```
 * yarn 
    ```sh
    yarn run tauri add upload
    ```
 * pnpm 
    ```sh
    pnpm tauri add upload
    ```
 * deno 
    ```sh
    deno task tauri add upload
    ```
 * bun 
    ```sh
    bun tauri add upload
    ```
 * cargo 
    ```sh
    cargo tauri add upload
    ```
 * Manual 
  ```sh
  npm run tauri add upload
  ```
 * npm 
  ```sh
  yarn run tauri add upload
  ```
 * yarn 
  ```sh
  pnpm tauri add upload
  ```
 * pnpm 
  ```sh
  deno task tauri add upload
  ```
 * deno 
  ```sh
  bun tauri add upload
  ```
 * bun 
  ```sh
  cargo tauri add upload
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-upload
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
       tauri::Builder::default()
         +.plugin(tauri_plugin_upload::init())
           .run(tauri::generate_context!())
           .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-upload
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-upload
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-upload
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-upload
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-upload
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-upload
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-upload
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-upload
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-upload
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-upload
  ```
 ## Usage Once you’ve completed the registration and setup process for the plugin, you can access all of its APIs through the JavaScript guest bindings. ### Upload `upload` sends the file as the raw request body (not `multipart/form-data`) and returns the response body as text: 
```javascript
import { upload } from '@tauri-apps/plugin-upload';
// when using `"withGlobalTauri": true`, you may use
// const { upload } = window.__TAURI__.upload;


const response = await upload(
  'https://example.com/file-upload',
  '/path/to/my/file.txt',
  ({ progressTotal, total }) =>
    console.log(`Uploaded ${progressTotal} of ${total} bytes`), // a callback that will be called with the upload progress
  { 'Content-Type': 'text/plain' } // optional headers to send with the request
);
```
 It sends a `POST` request by default. To use `PUT` or `PATCH`, pass an `HttpMethod` as the fifth argument: 
```javascript
import { upload, HttpMethod } from '@tauri-apps/plugin-upload';


await upload(
  'https://example.com/file-upload',
  '/path/to/my/file.txt',
  undefined, // no progress callback
  { 'Content-Type': 'text/plain' },
  HttpMethod.Put
);
```
 ### Download `download` saves the response body to the given file path: 
```javascript
import { download } from '@tauri-apps/plugin-upload';
// when using `"withGlobalTauri": true`, you may use
// const { download } = window.__TAURI__.upload;


await download(
  'https://example.com/file-download-link',
  '/path/to/save/my/file.txt',
  ({ progressTotal, total }) =>
    console.log(`Downloaded ${progressTotal} of ${total} bytes`), // a callback that will be called with the download progress
  { Authorization: 'Bearer <token>' } // optional headers to send with the request
);
```
 It sends a `GET` request by default. If you pass a body as the fifth argument, it sends a `POST` request with that body instead: 
```javascript
import { download } from '@tauri-apps/plugin-upload';


await download(
  'https://example.com/export',
  '/path/to/save/report.csv',
  undefined, // no progress callback
  { 'Content-Type': 'application/json' },
  JSON.stringify({ format: 'csv' })
);
```
 ### Progress The progress callback runs for each chunk and receives: * `progress`: bytes in the last chunk, not the running total * `progressTotal`: bytes transferred so far * `total`: total size in bytes. For downloads this comes from the `Content-Length` header and is `0` if the server doesn’t send it. * `transferSpeed`: approximate speed in bytes per second ### File paths Relative paths are resolved against the app’s working directory, which is different in `tauri dev` and in a bundled app. Use absolute paths instead, for example with the [path API](/reference/javascript/api/namespacepath/): 
```javascript
import { appDataDir, join } from '@tauri-apps/api/path';


const filePath = await join(await appDataDir(), 'file.txt');
```
 When downloading, the parent directory must already exist, and any existing file at that path is overwritten. If the download fails, the partial file is not removed. ### Errors Both functions reject if the file can’t be read or written, the request fails, or the server returns an error status. ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    ...,
    +"upload:default",
  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures what kind of operations are available from the upload plugin. #### [Granted Permissions](#granted-permissions) All operations are enabled by default. #### This default permission set includes the following: * `allow-upload` * `allow-download` ## Permission Table | Identifier | Description | | ----------------------- | -------------------------------------------------------------- | | `upload:allow-download` | Enables the download command without any pre-configured scope. | | `upload:deny-download` | Denies the download command without any pre-configured scope. | | `upload:allow-upload` | Enables the upload command without any pre-configured scope. | | `upload:deny-upload` | Denies the upload command without any pre-configured scope. |

# Websocket

> Open a WebSocket connection using a Rust client in JavaScript.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/websocket)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-websocket)[crates.io](https://crates.io/crates/tauri-plugin-websocket) API Reference:[](/reference/javascript/websocket/)[](https://docs.rs/tauri-plugin-websocket) Open a WebSocket connection using a Rust client in JavaScript. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the websocket plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add websocket
    ```
 * yarn 
    ```sh
    yarn run tauri add websocket
    ```
 * pnpm 
    ```sh
    pnpm tauri add websocket
    ```
 * deno 
    ```sh
    deno task tauri add websocket
    ```
 * bun 
    ```sh
    bun tauri add websocket
    ```
 * cargo 
    ```sh
    cargo tauri add websocket
    ```
 * Manual 
  ```sh
  npm run tauri add websocket
  ```
 * npm 
  ```sh
  yarn run tauri add websocket
  ```
 * yarn 
  ```sh
  pnpm tauri add websocket
  ```
 * pnpm 
  ```sh
  deno task tauri add websocket
  ```
 * deno 
  ```sh
  bun tauri add websocket
  ```
 * bun 
  ```sh
  cargo tauri add websocket
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-websocket
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.plugin(tauri_plugin_websocket::init())
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-websocket
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-websocket
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-websocket
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-websocket
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-websocket
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-websocket
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-websocket
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-websocket
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-websocket
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-websocket
  ```
 ## Usage The websocket plugin is available in JavaScript. 
```javascript
import WebSocket from '@tauri-apps/plugin-websocket';
// when using `"withGlobalTauri": true`, you may use
// const WebSocket = window.__TAURI__.websocket;


const ws = await WebSocket.connect('ws://127.0.0.1:8080');


const removeListener = ws.addListener((msg) => {
  console.log('Received Message:', msg);
});


await ws.send('Hello World!');


// optionally remove the listener
removeListener();


await ws.disconnect();
```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  +"permissions": ["websocket:default"]
}
```
 ## [Default Permission](#default-permission) Allows connecting and sending data to a WebSocket server #### This default permission set includes the following: * `allow-connect` * `allow-send` ## Permission Table | Identifier | Description | | ------------------------- | ------------------------------------------------------------- | | `websocket:allow-connect` | Enables the connect command without any pre-configured scope. | | `websocket:deny-connect` | Denies the connect command without any pre-configured scope. | | `websocket:allow-send` | Enables the send command without any pre-configured scope. | | `websocket:deny-send` | Denies the send command without any pre-configured scope. |

# Window State

> Persist window sizes and positions.

[GitHub](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/window-state)[npm](https://www.npmx.dev/package/@tauri-apps/plugin-window-state)[crates.io](https://crates.io/crates/tauri-plugin-window-state) API Reference:[](/reference/javascript/window-state/)[](https://docs.rs/tauri-plugin-window-state) Save window positions and sizes and restore them when the app is reopened. ## Supported Platforms *This plugin requires a Rust version of at least **1.90*** | Platform | Level | Notes | | -------- | ----- | ----- | | windows | | | | linux | | | | macos | | | | android | | | | ios | | | ## Setup Install the window-state plugin to get started. * Automatic Use your project’s package manager to add the dependency: * npm 
    ```sh
    npm run tauri add window-state
    ```
 * yarn 
    ```sh
    yarn run tauri add window-state
    ```
 * pnpm 
    ```sh
    pnpm tauri add window-state
    ```
 * deno 
    ```sh
    deno task tauri add window-state
    ```
 * bun 
    ```sh
    bun tauri add window-state
    ```
 * cargo 
    ```sh
    cargo tauri add window-state
    ```
 * Manual 
  ```sh
  npm run tauri add window-state
  ```
 * npm 
  ```sh
  yarn run tauri add window-state
  ```
 * yarn 
  ```sh
  pnpm tauri add window-state
  ```
 * pnpm 
  ```sh
  deno task tauri add window-state
  ```
 * deno 
  ```sh
  bun tauri add window-state
  ```
 * bun 
  ```sh
  cargo tauri add window-state
  ```
 * cargo 1. Run the following command in the `src-tauri` folder to add the plugin to the project’s dependencies in `Cargo.toml`: 
     ```sh
     cargo add tauri-plugin-window-state --target 'cfg(any(target_os = "macos", windows, target_os = "linux"))'
     ```
 2. Modify `lib.rs` to initialize the plugin: src-tauri/src/lib.rs 
     ```diff
     #[cfg_attr(mobile, tauri::mobile_entry_point)]
     pub fn run() {
         tauri::Builder::default()
             +.setup(|app| {
                 #[cfg(desktop)]
                 app.handle().plugin(tauri_plugin_window_state::Builder::default().build());
                 Ok(())
             })
             .run(tauri::generate_context!())
             .expect("error while running tauri application");
     }
     ```
 3. Install the JavaScript Guest bindings using your preferred JavaScript package manager: * npm 
       ```sh
       npm install @tauri-apps/plugin-window-state
       ```
 * yarn 
       ```sh
       yarn add @tauri-apps/plugin-window-state
       ```
 * pnpm 
       ```sh
       pnpm add @tauri-apps/plugin-window-state
       ```
 * deno 
       ```sh
       deno add npm:@tauri-apps/plugin-window-state
       ```
 * bun 
       ```sh
       bun add @tauri-apps/plugin-window-state
       ```
 * npm 
  ```sh
  npm install @tauri-apps/plugin-window-state
  ```
 * yarn 
  ```sh
  yarn add @tauri-apps/plugin-window-state
  ```
 * pnpm 
  ```sh
  pnpm add @tauri-apps/plugin-window-state
  ```
 * deno 
  ```sh
  deno add npm:@tauri-apps/plugin-window-state
  ```
 * bun 
  ```sh
  bun add @tauri-apps/plugin-window-state
  ```
 ## Usage After adding the window-state plugin, all windows will remember their state when the app is being closed and will restore to their previous state on the next launch. You can also access the window-state plugin in both JavaScript and Rust. ### JavaScript You can use `saveWindowState` to manually save the window state: 
```javascript
import { saveWindowState, StateFlags } from '@tauri-apps/plugin-window-state';
// when using `"withGlobalTauri": true`, you may use
// const { saveWindowState, StateFlags } = window.__TAURI__.windowState;


saveWindowState(StateFlags.ALL);
```
 Similarly you can manually restore a window’s state from disk: 
```javascript
import {
  restoreStateCurrent,
  StateFlags,
} from '@tauri-apps/plugin-window-state';
// when using `"withGlobalTauri": true`, you may use
// const { restoreStateCurrent, StateFlags } = window.__TAURI__.windowState;


restoreStateCurrent(StateFlags.ALL);
```
 ### Rust You can use the `save_window_state()` method exposed by the `AppHandleExt` trait: 
```rust
use tauri_plugin_window_state::{AppHandleExt, StateFlags};


// `tauri::AppHandle` now has the following additional method
app.save_window_state(StateFlags::all()); // will save the state of all open windows to disk
```
 Similarly you can manually restore a window’s state from disk using the `restore_state()` method exposed by the `WindowExt` trait: 
```rust
use tauri_plugin_window_state::{WindowExt, StateFlags};


// all `Window` types now have the following additional method
window.restore_state(StateFlags::all()); // will restore the window's state from disk
```
 ## Permissions By default all potentially dangerous plugin commands and scopes are blocked and cannot be accessed. You must modify the permissions in your `capabilities` configuration to enable these. See the [Capabilities Overview](/security/capabilities/) for more information and the [step by step guide](/learn/security/using-plugin-permissions/) to use plugin permissions. src-tauri/capabilities/default.json 
```diff
{
  "permissions": [
    ...,
    +"window-state:default",
  ]
}
```
 ## [Default Permission](#default-permission) This permission set configures what kind of operations are available from the window state plugin. #### [Granted Permissions](#granted-permissions) All operations are enabled by default. #### This default permission set includes the following: * `allow-filename` * `allow-restore-state` * `allow-save-window-state` ## Permission Table | Identifier | Description | | -------------------------------------- | ----------------------------------------------------------------------- | | `window-state:allow-filename` | Enables the filename command without any pre-configured scope. | | `window-state:deny-filename` | Denies the filename command without any pre-configured scope. | | `window-state:allow-restore-state` | Enables the restore_state command without any pre-configured scope. | | `window-state:deny-restore-state` | Denies the restore_state command without any pre-configured scope. | | `window-state:allow-save-window-state` | Enables the save_window_state command without any pre-configured scope. | | `window-state:deny-save-window-state` | Denies the save_window_state command without any pre-configured scope. |

# Security

> High-level concepts and security features at the core of Tauri's design and ecosystem that make you, your applications and your users more secure by default

This page is designed to explain the high-level concepts and security features at the core of Tauri’s design and ecosystem that make you, your applications and your users more secure by default. It also includes advice on best practices, how to report vulnerabilities to us and references to detailed concept explanations. Note It is important to remember that the security of your Tauri application is the sum of the overall security of Tauri itself, all Rust and npm dependencies, your code, and the devices that run the final application. The Tauri team does its best to do their part, the security community does its part and you should also follow some important best practices. ## Trust Boundaries > Trust boundary is a term used in computer science and security which describes a boundary where program data or execution changes its level of “trust,” or where two principals with different capabilities exchange data or commands. [1](#user-content-fn-wikipedia-trust-boundary) Tauri’s security model differentiates between Rust code written for the application’s core and frontend code written in any framework or language understood by the system WebView. Inspecting and strongly defining all data passed between boundaries is very important to prevent trust boundary violations. If data is passed without access control between these boundaries then it’s easy for attackers to elevate and abuse privileges. The [IPC layer](/concept/inter-process-communication/) is the bridge for communication between these two trust groups and ensures that boundaries are not broken. ![IPC Diagram](/_astro/tauri-trust-boundaries.C0cC9LAT_1KhzH4.svg) Any code executed by the plugins or the application core has full access to all available system resources and is not constrained. Any code executed in the WebView has only access to exposed system resources via the well-defined IPC layer. Access to core application commands is configured and restricted by capabilities defined in the application configuration. The individual command implementations enforce the optional fine-grained access levels also defined in the capabilities configuration. Learn more about the individual components and boundary enforcement: [Permissions](/security/permissions/) [Scopes](/security/scope/) [Capabilities](/security/capabilities/) [Runtime Authority](/security/runtime-authority/) Tauri allows developers to choose their own frontend stack and framework. This means that we cannot provide a hardening guide for every frontend stack of choice, but Tauri provides generic features to control and contain the attack surface. [Content Security Policy (CSP)](/security/csp/) [Isolation Pattern](/concept/inter-process-communication/isolation/) ## (Not) Bundling WebViews Tauri’s approach is to rely on the operating system WebView and not bundling the WebView into the application binary. This has a multitude of reasons but from a security perspective the most important reason is the average time it takes from publication of a security patched version of a WebView to being rolled out to the application end user. ![IPC Diagram](/_astro/tauri-update-lag.U0zyYit2_RPJXd.svg) We have observed that WebView package maintainers and operating system package maintainers are on average significantly faster to patch and roll out security patched Webview releases than application developers who bundle the WebView directly with their application. There are exceptions from this observation and in theory both paths can be taken in a similar time frame but this involves a larger overhead infrastructure for each application. Bundling has its drawbacks from a Tauri application developer experience and we do not think it is inherently insecure but the current design is a trade off that significantly reduces known vulnerabilities in the wild. ## Ecosystem The Tauri organization provides and maintains more than just the Tauri repository, and to ensure we provide a reasonable secure multi platform application framework, we make sure to go some extra miles. To learn more about how we secure our development process, what you could adapt and implement, what known threats your application can face and what we plan to improve or harden in the future, you can check out the following documents: [Ecosystem Security](/security/ecosystem/) [Application Lifecycle Threats](/security/lifecycle/) [Future Work](/security/future/) ## Coordinated Disclosure If you feel that there is a security concern or issue with anything in Tauri or other repositories in our organization, **please do not publicly comment on your findings**. Instead, reach out directly to our security team. The preferred disclosure method is via [Github Vulnerability Disclosure](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability#privately-reporting-a-security-vulnerability) on the affected repository. Most of our repositories have this feature enabled but if in doubt please submit via the [Tauri repository](https://github.com/tauri-apps/tauri/security/advisories/new). Alternatively you can contact us via email at: <security@tauri.app>. Although we do not currently have a budget for security bounties, in some cases, we will consider rewarding coordinated disclosure with our limited resources. ## Footnotes 1. <https://en.wikipedia.org/wiki/Trust_boundary>. [↩](#user-content-fnref-wikipedia-trust-boundary)

# Asset protocol scope

> Configure app.security.assetProtocol so the WebView can load local files safely, including FsScope, requireLiteralLeadingDot, and dynamic paths.

Tauri can serve files from disk into the WebView through the **asset** custom protocol (for example when you use [`convertFileSrc`](/reference/javascript/api/namespacecore/#convertfilesrc) in the frontend). Whether a path is allowed is controlled by **`app.security.assetProtocol`** in `tauri.conf.json`. You must set **`enable`** to `true` and define a **`scope`** that lists which filesystem paths may be exposed. Paths resolved at runtime must match that scope, or the WebView will refuse the load (often with an error such as “asset protocol not configured to allow the path”). Content Security Policy for `asset:` sources is documented on the [Content Security Policy (CSP)](/security/csp/) page. This page focuses on **scope** and how it interacts with globs and hidden path segments. ## How `scope` is defined `assetProtocol.scope` uses the same **`FsScope`** type as filesystem-related configuration elsewhere: either a **JSON array** of allowed glob patterns, or a **JSON object** with `allow`, optional `deny`, and optional `requireLiteralLeadingDot`. For how “scopes” fit into Tauri’s security model more broadly, see [Command scopes](/security/scope/). Patterns may start with a **base directory variable** (for example `$HOME`, `$CACHE`, `$APPCACHE`, `$APPDATA`, `$RESOURCE`). See the [path / base directory APIs](/reference/javascript/api/namespacepath/#basedirectory) for the full set of variables your app can rely on. Paths resolved when loading assets are usually **absolute** (on Linux, often under `/home/...`). A pattern like `["*/**"]` typically **does not** match those paths, because it does not line up with a leading `/` or a base-directory variable. Prefer patterns such as `$HOME/**/*`, `/home/username/**/*`, or another form that mirrors the resolved path. ### Array form (allowed paths only) Use a list when you only need a fixed allow list and default glob behavior is enough: src-tauri/tauri.conf.json 
```json
{
  "app": {
    "security": {
      "assetProtocol": {
        "enable": true,
        "scope": ["$APPCACHE/**/*", "$RESOURCE/**/*"]
      }
    }
  }
}
```
 With the array form you **cannot** set `requireLiteralLeadingDot`; for that, use the object form below. ### Object form (`allow`, `deny`, `requireLiteralLeadingDot`) Use an object when you need **deny** rules or to change **leading-dot** matching: src-tauri/tauri.conf.json 
```json
{
  "app": {
    "security": {
      "assetProtocol": {
        "enable": true,
        "scope": {
          "allow": ["$APPCACHE/**/*"],
          "deny": ["$APPCACHE/**/secrets/**"]
        }
      }
    }
  }
}
```
 `deny` takes precedence over `allow` when both match. ## Unix: path segments starting with `.` On Unix, `requireLiteralLeadingDot` defaults to **`true`**. Then wildcard tokens such as `*`, `?`, `**`, and `[...]` **do not match a path component that starts with** `.` (dotfiles and dot-directories such as `.cache` or `.ssh`). So a pattern like `$HOME/**` can allow `/home/user/Documents/file.png` but **not** `/home/user/.cache/myapp/preview.png`, because `.cache` is a dot-prefixed component. A pattern that names the segment literally (for example `$HOME/.cache/myapp/**`) **does** match. To allow dot-prefixed components under a broad glob, you can set **`requireLiteralLeadingDot`** to **`false`** on the **object** `scope` (this widens what the WebView can load; review carefully): src-tauri/tauri.conf.json 
```json
{
  "app": {
    "security": {
      "assetProtocol": {
        "enable": true,
        "scope": {
          "requireLiteralLeadingDot": false,
          "allow": ["$HOME/**/*"]
        }
      }
    }
  }
}
```
 ## Prefer `**/*` over bare `**` for “all files under here” For globs that should match **files** under a tree, prefer `**/*` (and variants like `$DIR/**/*`) rather than bare `**`, consistent with other Tauri path examples. Bare `**` is easy to misuse when you intend “everything under this directory recursively.” ## Highly permissive configuration (use with extreme care) If you intentionally need the broadest possible access **and** dot-prefixed segments, a maintainer-suggested shape looks like this. **This is not a default recommendation**; it increases exposure of hidden and sensitive files. src-tauri/tauri.conf.json 
```json
{
  "app": {
    "security": {
      "assetProtocol": {
        "enable": true,
        "scope": {
          "requireLiteralLeadingDot": false,
          "allow": ["**/*"]
        }
      }
    }
  }
}
```
 Caution Prefer **narrow** directories (`$APPCACHE`, `$RESOURCE`, a single app subfolder under `$HOME`, etc.) instead of broad `$HOME/**/*` or `**/*` unless you have a strong reason and understand the security tradeoffs. ## Static config vs dynamically chosen paths Entries in **`tauri.conf.json`** describe **static** allow/deny patterns. They do not replace runtime workflows where the user picks arbitrary folders or files (for example with the **dialog** plugin): those paths may need to be **persisted** across restarts using the [**persisted-scope**](/plugin/persisted-scope/) plugin. To persist **asset** / protocol-related scope with that plugin, enable its **`protocol-asset`** Cargo feature in `src-tauri/Cargo.toml`, for example: 
```toml
tauri-plugin-persisted-scope = { version = "2", features = ["protocol-asset"] }
```
 Register **`tauri_plugin_fs`** before **`tauri_plugin_persisted_scope`** as described in the plugin guide. ## Troubleshooting | Symptom | Things to check | | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | | “asset protocol not configured to allow the path” | Path must match an **`allow`** pattern; **`deny`** overrides **`allow`**. Use **absolute** patterns or **`$VAR`/`$HOME`** style variables that match how the path is resolved on disk. | | Works for normal folders but not under **`.cache`** / **`.config`** | On Unix, default **`requireLiteralLeadingDot`** behavior: use a literal `.segment` in the pattern, or set **`requireLiteralLeadingDot`: `false`** in the object `scope` (see [tauri#13788](https://github.com/tauri-apps/tauri/issues/13788)). | | User picked a folder at runtime; still blocked after restart | You may need [**persisted-scope**](/plugin/persisted-scope/) with the **`protocol-asset`** feature, not only `tauri.conf.json` entries. | | Broad `**` seems wrong | Try `**/*` for file-oriented globs; see [Embedding Additional Files](/develop/resources/) for similar `**` vs `**/*` guidance in bundle resources. | | Scope like `["*/**"]` never matches on Linux | Resolved paths are **absolute**; use **`$...` variables**, a leading **`/`**, or another pattern that matches the real path (see above). | The authoritative Rust types for `assetProtocol` and `FsScope` live in Tauri’s [`config.rs`](https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-utils/src/config.rs) (`AssetProtocolConfig`, `FsScope`). The generated [configuration reference](/reference/config/) may render nested `FsScope` fields in a compact or hard-to-read way; if something looks unclear there, cross-check this page and the [file system plugin](/plugin/file-system/) `requireLiteralLeadingDot` section (plugin config uses the same option name for its own scopes). If the reference still does not document those fields clearly, consider opening an issue on the **tauri-docs** repository so the config generator can be improved.

# Capabilities

Tauri provides application and plugin developers with a capabilities system, to granularly enable and constrain the core exposure to the application frontend running in the system WebView. Capabilities define which [permissions](/security/permissions/) are granted or denied for which windows or webviews. Capabilities can affect multiple windows and webviews and these can be referenced in multiple capabilities. Capability files are either defined as a JSON or a TOML file inside the `src-tauri/capabilities` directory. It is good practice to use individual files and only reference them by identifier in the `tauri.conf.json` but it is also possible to define them directly in the `capabilities` field. All capabilities inside the `capabilities` directory are automatically enabled by default. Once capabilities are explicitly enabled in the `tauri.conf.json`, only these are used in the application build. For a full reference of the configuration scheme please see the [references](/reference/config/) section. The following example JSON defines a capability that allows the main window use the default functionality of core plugins and the `window.setTitle` API. src-tauri/capabilities/default.json 
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:path:default",
    "core:event:default",
    "core:window:default",
    "core:app:default",
    "core:resources:default",
    "core:menu:default",
    "core:tray:default",
    "core:window:allow-set-title"
  ]
}
```
 These snippets are part of the [Tauri configuration](/develop/configuration-files/#tauri-config) file. This is likely the most common configuration method, where the individual capabilities are inlined and only permissions are referenced by identifier. This requires well-defined capability files in the `capabilities` directory. src-tauri/tauri.conf.json 
```json
{
  "app": {
    "security": {
      "capabilities": ["my-capability", "main-capability"]
    }
  }
}
```
 Inline capabilities can be mixed with pre-defined capabilities. src-tauri/tauri.conf.json 
```json
{
  "app": {
    "security": {
      "capabilities": [
        {
          "identifier": "my-capability",
          "description": "My application capability used for all windows",
          "windows": ["*"],
          "permissions": ["fs:default", "allow-home-read-extended"]
        },
        "my-second-capability"
      ]
    }
  }
}
```
 By default, all commands that you registered in your app (using the [`tauri::Builder::invoke_handler`](https://docs.rs/tauri/2.0.0/tauri/struct.Builder.html#method.invoke_handler) function) are allowed to be used by all the windows and webviews of the app. To change that, consider using [`AppManifest::commands`](https://docs.rs/tauri-build/2.0.0/tauri_build/struct.AppManifest.html#method.commands). src-tauri/build.rs 
```rust
fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&["your_command"])),
    )
    .unwrap();
}
```
 ## Target Platform Capabilities can be platform-specific by defining the `platforms` array. By default the capability is applied to all targets, but you can select a subset of the `linux`, `macOS`, `windows`, `iOS` and `android` targets. For example a capability for desktop operating systems. Note it enables permissions on plugins that are only available on desktop: src-tauri/capabilities/desktop.json 
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "desktop-capability",
  "windows": ["main"],
  "platforms": ["linux", "macOS", "windows"],
  "permissions": ["global-shortcut:allow-register"]
}
```
 And another example of a capability for mobile. Note it enables permissions on plugins that are only available on mobile: src-tauri/capabilities/mobile.json 
```json
{
  "$schema": "../gen/schemas/mobile-schema.json",
  "identifier": "mobile-capability",
  "windows": ["main"],
  "platforms": ["iOS", "android"],
  "permissions": [
    "nfc:allow-scan",
    "biometric:allow-authenticate",
    "barcode-scanner:allow-scan"
  ]
}
```
 ## Remote API Access By default the API is only accessible to bundled code shipped with the Tauri App. To allow remote sources access to certain Tauri Commands it is possible to define this in the capability configuration file. This example would allow to scan for NFC tags and to use the barcode scanner from all subdomains of `tauri.app`. src-tauri/capabilities/remote-tags.json 
```json
{
  "$schema": "../gen/schemas/remote-schema.json",
  "identifier": "remote-tag-capability",
  "windows": ["main"],
  "remote": {
    "urls": ["https://*.tauri.app"]
  },
  "platforms": ["iOS", "android"],
  "permissions": ["nfc:allow-scan", "barcode-scanner:allow-scan"]
}
```
 Caution On Linux and Android, Tauri is unable to distinguish between requests from an embedded `<iframe>` and the window itself. Please consider usage of this feature very carefully and read more into the specific security implications for your targeted operating system in the reference section of this feature. ## Security Boundaries *What does it protect against?* Depending on the permissions and capabilities it is able to: * Minimize impact of frontend compromise * Prevent or reduce (accidental) exposure of local system interfaces and data * Prevent or reduce possible privilege escalation from frontend to backend/system *What does it **not** protect against?* * Malicious or insecure Rust code * Too lax scopes and configuration * Incorrect scope checks in the command implementation * Intentional bypasses from Rust code * Basically anything which was written in the rust core of an application * 0-days or unpatched 1-days in the system WebView * Supply chain attacks or otherwise compromised developer systems ## Schema Files Tauri generates JSON schemas with all the permissions available to your application through `tauri-build`, allowing autocompletion in your IDE. To use a schema, set the `$schema` property in your configuration file (either .json or .toml) to one of the platform-specific schemas located in the `gen/schemas` directory. Usually you will set it to `../gen/schemas/desktop-schema.json` or `../gen/schemas/mobile-schema.json` though you can also define a capability for a specific target platform. ## Configuration Files Simplified example of an example Tauri application directory structure: 
```sh
tauri-app
├── index.html
├── package.json
├── src/
├── src-tauri/
│   ├── Cargo.toml
│   ├── capabilities/
│   │  └── <identifier>.json/toml
│   ├── src/
│   ├── tauri.conf.json
```
 Everything can be inlined into the `tauri.conf.json` but even a little more advanced configuration would bloat this file and the goal of this approach is that the permissions are abstracted away whenever possible and simple to understand. ## Core Permissions A list of all core permissions can be found on the [Core Permissions](/reference/acl/core-permissions/) page.

# Content Security Policy (CSP)

Tauri restricts the [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP) (CSP) of your HTML pages. This can be used to reduce or prevent impact of common web based vulnerabilities like cross-site-scripting (XSS). Local scripts are hashed, styles and external scripts are referenced using a cryptographic nonce, which prevents unallowed content from being loaded. Caution Avoid loading remote content such as scripts served over a CDN as they introduce an attack vector. In general any untrusted file can introduce new and subtle attack vectors. The CSP protection is only enabled if set on the Tauri configuration file. You should make it as restricted as possible, only allowing the webview to load assets from hosts you trust, and preferably own. At compile time, Tauri appends its nonces and hashes to the relevant CSP attributes automatically to bundled code and assets, so you only need to worry about what is unique to your application. This is an example CSP configuration taken from the [`api`](https://github.com/tauri-apps/tauri/blob/dev/examples/api/src-tauri/tauri.conf.json#L22) example of Tauri, but every application developer needs to tailor this to their own application needs. tauri/examples/api/src-tauri/tauri.conf.json 
```json
  "csp": {
        "default-src": "'self' customprotocol: asset:",
        "connect-src": "ipc: http://ipc.localhost",
        "font-src": ["https://fonts.gstatic.com"],
        "img-src": "'self' asset: http://asset.localhost blob: data:",
        "style-src": "'unsafe-inline' 'self' https://fonts.googleapis.com"
      },
```
 See [`script-src`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/script-src), [`style-src`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/style-src) and [CSP Sources](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/Sources#sources) for more information about this protection.

# Tauri Ecosystem Security

Our Tauri organization ecosystem is hosted on GitHub and facilitates several features to make our repositories more resilient against adversaries targeting our source code and releases. To reduce risk and to comply with commonly adopted best practices we have the following methods in place. ### Build Pipelines The process of releasing our source-code artifacts is highly automated in GitHub build pipelines using GitHub actions, yet mandates kickoff and review from real humans. ### Signed Commits Our core repositores require signed commits to reduce risk of impersonation and to allow identification of attributed commits after detection of possible compromise. ### Code Review All Pull Requests (PRs) merged into our repositories need approval from at least one maintainer of the project, which in most cases is the working group. Code is generally reviewed in PRs and default security workflows and checks are run to ensure the code adheres to common standards. ### Release Process Our working group reviews code changes, tags PRs with scope, and makes sure that everything stays up to date. We strive to internally audit all security relevant PRs before publishing minor and major releases. And when its time to publish a new version, one of the maintainers tags a new release on dev, which: * Validates core * Runs tests * Audits security for crates and npm * Generates changelogs * Creates artifacts * Creates a draft release Then the maintainer reviews the release notes, edits if necessary, and a new release is forged.

# Future Work

This section describes topics we started or would like to tackle in the future to make Tauri apps even more secure. If you feel interested in these topics or have pre-existing knowledge we are always happy to welcome new contributors and advice via GitHub or other community platforms like Discord. ### Binary Analysis To allow pentesters, auditors and automated security checks do to their job properly it is very valuable to provide insight even from compiled binaries. Not all companies are open source or provide source code for audits, red-teams and other security testing. Another often overlooked point is that providing inbuilt metadata empowers users of your application to audit their systems for known vulnerabilities at scale without dedicating their lifetime and efforts into it. If your threatmodel depends on security by obscurity this section will be providing some tools and points which hopefully will make you reconsider. For Rust there is `cargo-auditable` to create [SBOMs](https://en.wikipedia.org/wiki/Software_supply_chain) and provide exact crate versions and dependencies of a binary without breaking reproducible builds. For the frontend stack we are not aware of similar solutions, so extracting the frontend assets from the binary should be a straightforward process. Afterwards it should be possible to use tooling like `npm audit` or similar. There are already [blog posts](https://infosecwriteups.com/reverse-engineering-a-native-desktop-application-tauri-app-5a2d92772da5) about the process but no simple tooling is available. We are planning to provide such tooling or make it easier to extract assets, when compiling a Tauri app with certain features. To use pentesting tools like [Burpsuite](https://portswigger.net/burp), [Zap](https://www.zaproxy.org/) or [Caido](https://caido.io/) it is necessary to intercept traffic from the webview and pass it through the testing proxy. Currently Tauri has no inbuilt method to do so but there is ongoing work to ease this process. All of these tools allow to properly test and inspect Tauri applications without source code access and should be considered when building a Tauri application. We are planning to further support and implement related features in the future. ### WebView Hardening In Tauri’s current threat model and boundaries we are not able to add more security constraints to the WebView itself and since it is the biggest part of our stack which is written in a memory unsafe language, we are planning to research and consider ways to further sandbox and isolate the webview processes. Inbuilt and external sandboxing methods will be evaluated to reduce attack impact and to enforce the IPC bridge for system access. We believe that this part of our stack is the weak link but current generation WebViews are improving in their hardening and exploit resilience. ### Fuzzing To allow more efficient and simplify the process of fuzzing Tauri applications we aim to further implement our mock runtimes and other tooling to make it easier to configure and build for individual Tauri applications. Tauri is supporting a multitude of Operating Systems and CPU architectures, usually apps have only few or no possible memory unsafe code. No pre-existing fuzzing tooling and libraries support these uncommon fuzzing use case, so we need to implement it and support existing libraries like [libAFL](https://github.com/AFLplusplus/LibAFL) to build Tauri fuzzing frameworks. The goal is to make fuzzing accessible and efficient for Tauri application developers.

# HTTP Headers

[Since `2.1.0`](https://v2.tauri.app/release/tauri/v2.1.0/) A header defined in the configuration gets sent along the responses to the webview. This doesn’t include IPC messages and error responses. To be more specific, every response sent via the `get_response` function in [crates/tauri/src/protocol/tauri.rs ↗](https://github.com/tauri-apps/tauri/blob/8e8312bb8201ccc609e4bbc1a990bdc314daa00f/crates/tauri/src/protocol/tauri.rs#L103) will include those headers. ### Header Names The header names are limited to: * [Access-Control-Allow-Credentials ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Credentials) * [Access-Control-Allow-Headers ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Headers) * [Access-Control-Allow-Methods ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Methods) * [Access-Control-Expose-Headers ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Expose-Headers) * [Access-Control-Max-Age ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Max-Age) * [Cross-Origin-Embedder-Policy ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy) * [Cross-Origin-Opener-Policy ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Opener-Policy) * [Cross-Origin-Resource-Policy ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Resource-Policy) * [Permissions-Policy ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy) * [Service-Worker-Allowed ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Service-Worker-Allowed) * [Timing-Allow-Origin ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Timing-Allow-Origin) * [X-Content-Type-Options ↗](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Content-Type-Options) * Tauri-Custom-Header Note `Tauri-Custom-Header` is not intended for production use. Note [The Content-Security-Policy (CSP)](../csp/) is not defined here. ### How to Configure Headers * with a string * with an array of strings * with an object/key-value, where the values must be strings * with null The header values are always converted to strings for the actual response. Depending on how the configuration file looks, some header values need to be composed. Those are the rules on how a composite gets created: * `string`: stays the same for the resulting header value * `array`: items are joined by `, `for the resulting header value * `key-value`: items are composed from: key + space + value. Items are then joined by `; `for the resulting header value * `null`: header will be ignored ### Example src-tauri/tauri.conf.json 
```javascript
{
 //...
  "app":{
    //...
    "security": {
      //...
      "headers": {
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Timing-Allow-Origin": [
          "https://developer.mozilla.org",
          "https://example.com",
        ],
        "X-Content-Type-Options": null, // gets ignored
        "Access-Control-Expose-Headers": "Tauri-Custom-Header",
        "Tauri-Custom-Header": {
          "key1": "'value1' 'value2'",
          "key2": "'value3'"
        }
      },
      // notice how the CSP is not defined under headers
      "csp": "default-src 'self'; connect-src ipc: http://ipc.localhost",
    }
  }
}
```
 Note `Tauri-Custom-Header` is not intended for production use. For Tests: Remember to set `Access-Control-Expose-Headers` accordingly. In this example `Cross-Origin-Opener-Policy` and `Cross-Origin-Embedder-Policy` are set to allow for the use of [`SharedArrayBuffer ↗`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer). `Timing-Allow-Origin` grants scripts loaded from the listed websites to access detailed network timing data via the [Resource Timing API ↗](https://developer.mozilla.org/en-US/docs/Web/API/Performance_API/Resource_timing). For the helloworld example, this config results in: 
```http
access-control-allow-origin:  http://tauri.localhost
access-control-expose-headers: Tauri-Custom-Header
content-security-policy: default-src 'self'; connect-src ipc: http://ipc.localhost; script-src 'self' 'sha256-Wjjrs6qinmnr+tOry8x8PPwI77eGpUFR3EEGZktjJNs='
content-type: text/html
cross-origin-embedder-policy: require-corp
cross-origin-opener-policy: same-origin
tauri-custom-header: key1 'value1' 'value2'; key2 'value3'
timing-allow-origin: https://developer.mozilla.org, https://example.com
```
 ### Frameworks Some development environments require extra settings, to emulate the production environment. Note In order to get headers to work for these frameworks, you may need to define them in both the framework’s configuration (for development mode) and the Tauri config (for build mode). This is because: * The frameworks won’t include headers defined in their config files at build time. * Tauri can’t inject headers into the framework’s dev server – it can only inject headers to the final build output. #### JavaScript/TypeScript For setups running the build tool **Vite** (those include **Qwik, React, Solid, Svelte, and Vue**) add the wanted headers to `vite.config.ts`. vite.config.ts 
```typescript
import { defineConfig } from 'vite';


export default defineConfig({
  // ...
  server: {
      // ...
      headers: {
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Timing-Allow-Origin': 'https://developer.mozilla.org, https://example.com',
        'Access-Control-Expose-Headers': 'Tauri-Custom-Header',
        'Tauri-Custom-Header': "key1 'value1' 'value2'; key2 'value3'"
      },
    },
})
```
 Sometimes the `vite.config.ts` is integrated into the frameworks configuration file, but the setup stays the same. In case of **Angular** add them to `angular.json`. angular.json 
```json
{
  //...
  "projects":{
    //...
    "insert-project-name":{
      //...
      "architect":{
        //...
        "serve":{
          //...
          "options":{
            //...
            "headers":{
              "Cross-Origin-Opener-Policy": "same-origin",
              "Cross-Origin-Embedder-Policy": "require-corp",
              "Timing-Allow-Origin": "https://developer.mozilla.org, https://example.com",
              "Access-Control-Expose-Headers": "Tauri-Custom-Header",
              "Tauri-Custom-Header": "key1 'value1' 'value2'; key2 'value3'"
            }
          }
        }
      }
    }
  }
}
```
 And in case of **Nuxt** to `nuxt.config.ts`. nuxt.config.ts 
```typescript
export default defineNuxtConfig({
  //...
  vite: {
    //...
    server: {
      //...
      headers:{
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Timing-Allow-Origin': 'https://developer.mozilla.org, https://example.com',
        'Access-Control-Expose-Headers': 'Tauri-Custom-Header',
        'Tauri-Custom-Header': "key1 'value1' 'value2'; key2 'value3'"
      }
    },
  },
});
```
 **Next.js** doesn’t rely on **Vite**, so the approach is different. Read more about it [here ↗](https://nextjs.org/docs/pages/api-reference/next-config-js/headers). The headers are defined in `next.config.js`. next.config.js 
```javascript
module.exports = {
  //...
  async headers() {
    return [
      {
        source: '/*',
        headers: [
          {
            key: 'Cross-Origin-Opener-Policy',
            value: 'same-origin',
          },
          {
            key: 'Cross-Origin-Embedder-Policy',
            value: 'require-corp',
          },
          {
            key: 'Timing-Allow-Origin',
            value: 'https://developer.mozilla.org, https://example.com',
          },
          {
            key: 'Access-Control-Expose-Headers',
            value: 'Tauri-Custom-Header',
          },
          {
            key: 'Tauri-Custom-Header',
            value: "key1 'value1' 'value2'; key2 'value3'",
          },
        ],
      },
    ]
  },
}
```
 #### Rust For **Yew** and **Leptos** add the headers to `Trunk.toml` Trunk.toml 
```toml
#...
[serve]
#...
headers = {
  "Cross-Origin-Opener-Policy" = "same-origin",
  "Cross-Origin-Embedder-Policy" = "require-corp",
  "Timing-Allow-Origin" = "https://developer.mozilla.org, https://example.com",
  "Access-Control-Expose-Headers" = "Tauri-Custom-Header",
  "Tauri-Custom-Header" = "key1 'value1' 'value2'; key2 'value3'"
}
```

# Application Lifecycle Threats

Tauri applications are composed of many pieces at different points in time of the application lifecycle. Here we describe classical threats and what you SHOULD do about them. All of these distinct steps are described in the following sections. ![Threat Stages During Development](/_astro/application-flow-simple.X8I9EoEI_Z29dtSA.svg) Note The weakest link in your application lifecycle essentially defines your security. Each step can compromise the assumptions and integrity of all subsequent steps, so it is important to see the whole picture at all times. ## Upstream Threats Tauri is a direct dependency on your project, and we maintain strict authorial control of commits, reviews, pull requests, and releases. We do our best to maintain up-to-date dependencies and take action to either update or fork and fix. Other projects may not be so well maintained, and may not even have ever been audited. Please consider their health when integrating them, otherwise, you may have adopted architectural debt without even knowing it. ### Keep Your Applications Up-To-Date When releasing your app into the wild, you are also shipping a bundle that has Tauri in it. Vulnerabilities affecting Tauri may impact the security of your application. By updating Tauri to the latest version, you ensure that critical vulnerabilities are already patched and cannot be exploited in your application. Also be sure to keep your compiler (`rustc`) and transpilers (`nodejs`) up to date, because there are often security issues that are resolved. This also is true for your development system in general. ### Evaluate Your Dependencies While NPM and Crates.io provide many convenient packages, it is your responsibility to choose trustworthy third-party libraries - or rewrite them in Rust. If you do use outdated libraries which are affected by known vulnerabilities or are unmaintained, your application security and good night’s sleep could be in jeopardy. Use tooling like [`npm audit`](https://docs.npmjs.com/cli/v10/commands/npm-audit) and [`cargo audit`](https://crates.io/crates/cargo-audit) to automate this process, and lean on the security community’s important work. Recent trends in the rust ecosystem like [`cargo-vet`](https://github.com/mozilla/cargo-vet) or [`cargo crev`](https://github.com/crev-dev/cargo-crev) can help to further reduce likelihood of supply chain attacks. To find out on whose shoulders you stand, you can use the [`cargo supply chain`](https://github.com/rust-secure-code/cargo-supply-chain) tool. One practice that we highly recommend, is to only ever consume critical dependencies from git using hash revisions at best or named tags as second best. This holds for Rust as well as the Node ecosystem. ## Development Threats We assume that you, the developer, care for your development environment. It is on you to make sure that your operating system, build toolchains, and associated dependencies are kept up to date and reasonable secured. A genuine risk all of us face is what is known as “supply-chain attacks”, which are usually considered to be attacks on direct dependencies of your project. However, a growing class of attacks in the wild directly target development machines, and you would be well off to address this head-on. ### Development Server Tauri application frontends can be developed using a number of web frameworks. Each of these frameworks usually ship their own development server, which is exposing the frontend assets via an open port to the local system or network. This allows the frontend to be hot-reloaded and debugged in the WebView or Browser. In practice this connection is often neither encrypted nor authenticated by default. This is also the case for the built-in Tauri development server and exposes your frontend and assets to the local network. Additionally, this allows attackers to push their own frontend code to development devices in the same network as the attacker. Depending on what kind of functionality is exposed this could lead to device compromise in the worst case. You should only develop on trusted networks where you can safely expose your development device. If this is not possible you MUST ensure that your development server uses **mutual** authentication and encryption (e.g. mTLS) for connections with your development devices. Note The built-in Tauri development server does not support mutual authentication and transport encryption at the moment and should not be used on untrusted networks. ### Harden Development machines Hardening your development systems depends on various factors and on your personal threat model but some generic advice we recommend to follow: * Never use administrative accounts for day to day tasks like coding * Never use production secrets on development machines * Prevent secrets to be checked into source code version control * Use security hardware tokens or similar to reduce impact of compromised systems * Keep your system up to date * Keep your installed applications to a minimum A more practical collection of procedures can be found in an [awesome security hardening collection](https://github.com/decalage2/awesome-security-hardening). You can of course virtualise your development environment to keep attackers at bay, but this won’t protect you from attacks that target your project rather than just your machine. ### Ensure Source Control Authentication and Authorization If you are working like the majority of developers, using source code version control tools and service providers is an essential step during development. To ensure that your source code can not be modified by unauthorized actors it is important to understand and correctly set up access control for your source code version control system. Also, consider requiring all (regular) contributors to sign their commits to prevent situations where malicious commits are attributed to non-compromised or non-malicious contributors. ## Buildtime Threats Modern organizations use CI/CD to manufacture binary artifacts. You need to be able to fully trust these remote (and third party owned) systems, as they have access to source code, secrets and are able to modify builds without you being able to verifiably prove that the produced binaries are the same as your local code. This means either you trust a reputable provider or host these systems on your own and controlled hardware. At Tauri, we provide a GitHub Workflow for building on multiple platforms. If you create your own CI/CD and depend on third-party tooling, be wary of actions whose versions you have not explicitly pinned. You should sign your binaries for the platform you are shipping to. While this can be complicated and somewhat costly to set up, end users expect that your app is verifiably from you. If cryptographic secrets are properly stored on hardware tokens, a compromised build system won’t be able to leak involved signing keys, but could use them to sign malicious releases. ### Reproducible Builds To combat backdoor injection at build time, you need your builds to be reproducible, so that you can verify that the build assets are exactly the same when you build them locally or on another independent provider. The first problem is that Rust is by default not fully **reliably** producing reproducible builds. It supports this in theory, but there are still bugs, and it recently broke on a release. You can keep track of the current state in the rust project’s [public bug tracker](https://github.com/rust-lang/rust/labels/A-reproducibility). The next problem you will encounter is that many common frontend bundlers do not produce reproducible output either, so the bundled assets may also break reproducible builds. This means that you cannot fully rely on reproducible builds by default, and sadly need to fully trust your build systems. ## Distribution Threats We have done our best to make shipping hot updates to the app as straightforward and secure as possible. However, all bets are off if you lose control of the manifest server, the build server, or the binary hosting service. If you build your own system, consult a professional OPS architect and build it properly. If you are looking for another trusted distribution solution for Tauri apps our partner CrabNebula has an offering: <https://crabnebula.dev/cloud> ## Runtime Threats We assume the webview is insecure, which has led Tauri to implement several protections regarding webview access to system APIs in the context of loading untrusted userland content. Using the [Content Security Policy](/security/csp/) will lockdown types of communication that the Webview can undertake. Furthermore, [Capabilities](/security/capabilities/) can prevent untrusted content or scripts from accessing the API within the Webview. We also recommend to setup an easy and secure way to report vulnerabilities similar to [our process](/security/#coordinated-disclosure).

# Permissions

Permissions are descriptions of explicit privileges of commands. 
```toml
[[permission]]
identifier = "my-identifier"
description = "This describes the impact and more."
commands.allow = [
    "read_file"
]


[[permission.scope.allow]]
my-scope = "$HOME/*"


[[permission.scope.deny]]
my-scope = "$HOME/secret"
```
 It can enable commands to be accessible in the frontend of a Tauri application. It can map scopes to commands and defines which commands are enabled. Permissions can enable or deny certain commands, define scopes or combine both. To grant or deny a permission to your app’s window or webview, you must reference the permission in a [capability](/security/capabilities/). Permissions can be grouped as a set under a new identifier. This is called a permission set. This allows you to combine scope related permissions with command related permissions. It also allows to group or bundle operating specific permissions into more usable sets. As a plugin developer you can ship multiple, pre-defined, well named permissions for all of your exposed commands. As an application developer you can extend existing plugin permissions or define them for your own commands. They can be grouped or extended in a set to be re-used or to simplify the main configuration files later. ## Permission Identifier The permissions identifier is used to ensure that permissions can be re-used and have unique names. * `<name>:default` Indicates the permission is the default for a plugin or application * `<name>:<command-name>` Indicates the permission is for an individual command The plugin prefix `tauri-plugin-` will be automatically prepended to the identifier of plugins at compile time and is not required to be manually specified. Identifiers are limited to ASCII lower case alphabetic characters `[a-z]` and the maximum length of the identifier is currently limited to `116` due to the following constants: 
```rust
const IDENTIFIER_SEPARATOR: u8 = b':';
const PLUGIN_PREFIX: &str = "tauri-plugin-";


// https://doc.rust-lang.org/cargo/reference/manifest.html#the-name-field
const MAX_LEN_PREFIX: usize = 64 - PLUGIN_PREFIX.len();
const MAX_LEN_BASE: usize = 64;
const MAX_LEN_IDENTIFIER: usize = MAX_LEN_PREFIX + 1 + MAX_LEN_BASE;
```
 ## Configuration Files Simplified example of an example Tauri **plugin** directory structure: 
```sh
tauri-plugin
├── README.md
├── src
│  └── lib.rs
├── build.rs
├── Cargo.toml
├── permissions
│  └── <identifier>.json/toml
│  └── default.json/toml
```
 The default permission is handled in a special way, as it is automatically added to the application configuration, as long as the Tauri CLI is used to add plugins to a Tauri application. For **application** developers the structure is similar: 
```sh
tauri-app
├── index.html
├── package.json
├── src
├── src-tauri
│   ├── Cargo.toml
│   ├── permissions
│      └── <identifier>.toml
|   ├── capabilities
│      └── <identifier>.json/.toml
│   ├── src
│   ├── tauri.conf.json
```
 Note As an application developer the capability files can be written in `json`/`json5` or `toml`, whereas permissions only can be defined in `toml`. ## Examples Example permissions from the `File System` plugin. plugins/fs/permissions/autogenerated/base-directories/home.toml 
```toml
[[permission]]
identifier = "scope-home"
description = """This scope permits access to all files and
list content of top level directories in the `$HOME`folder."""


[[permission.scope.allow]]
path = "$HOME/*"
```
 plugins/fs/permissions/read-files.toml 
```toml
[[permission]]
identifier = "read-files"
description = """This enables all file read related
commands without any pre-configured accessible paths."""
commands.allow = [
    "read_file",
    "read",
    "open",
    "read_text_file",
    "read_text_file_lines",
    "read_text_file_lines_next"
]
```
 plugins/fs/permissions/autogenerated/commands/mkdir.toml 
```toml
[[permission]]
identifier = "allow-mkdir"
description = "This enables the mkdir command."
commands.allow = [
    "mkdir"
]
```
 Example implementation extending above plugin permissions in your app: my-app/src-tauri/permissions/home-read-extends.toml 
```toml
[[set]]
identifier = "allow-home-read-extended"
description = """ This allows non-recursive read access to files and to create directories
in the `$HOME` folder.
"""
permissions = [
    "fs:read-files",
    "fs:scope-home",
    "fs:allow-mkdir"
]
```

# Runtime Authority

The runtime authority is part of the Tauri Core. It holds all permissions, capabilities and scopes at runtime to enforce which window can access which command and passes scopes to commands. Whenever a Tauri command is invoked from the webview the runtime authority receives the invoke request, makes sure that the origin is allowed to actually use the requested command, checks if the origin is part of capabilities and if scopes are defined for the command and applicable then they are injected into the invoke request, which is then passed to the proper Tauri command. If the origin is not allowed to call the command, the runtime authority will deny the request and the Tauri command is never invoked. ![IPC Diagram](/_astro/runtime-authority.97JqQbdT_Z1M2l65.svg)

# Command Scopes

A scope is a granular way to define (dis)allowed behavior of a Tauri command. Scopes are categorized into `allow` or `deny` scopes, where `deny` always supersedes the `allow` scope. The scope type needs be of any [`serde`](https://docs.rs/serde/latest/serde/) serializable type. These types are plugin-specific in general. For scoped commands implemented in a Tauri application the scope type needs to be defined in the application and then enforced in the command implementation. For instance, the [`Fs`](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/fs) plugin allows you to use scopes to allow or deny certain directories and files and the [`http`](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/http) plugin uses scopes to filter URLs that are allowed to be reached. The scope is passed to the command and handling or properly enforcing is implemented by the command itself. Caution Command developers need to ensure that there are no scope bypasses possible. The scope validation implementation should be audited to ensure correctness. ## Examples These examples are taken from the [`Fs`](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/fs) plugin permissions: The scope type in this plugin for all commands is a string, which contains a [`glob`](https://docs.rs/glob/latest/glob/) compatible path. plugins/fs/permissions/autogenerated/base-directories/applocaldata.toml 
```toml
[[permission]]
identifier = "scope-applocaldata-recursive"
description = '''
This scope recursive access to the complete `$APPLOCALDATA` folder,
including sub directories and files.
'''


[[permission.scope.allow]]
path = "$APPLOCALDATA/**"
```
 plugins/fs/permissions/deny-webview-data.toml 
```toml
[[permission]]
identifier = "deny-webview-data-linux"
description = '''
This denies read access to the
`$APPLOCALDATA` folder on linux as the webview data and
configuration values are stored here.
Allowing access can lead to sensitive information disclosure and
should be well considered.
'''
platforms = ["linux"]


[[permission.scope.deny]]
path = "$APPLOCALDATA/**"


[[permission]]
identifier = "deny-webview-data-windows"
description = '''
This denies read access to the
`$APPLOCALDATA/EBWebView` folder on windows as the webview data and
configuration values are stored here.
Allowing access can lead to sensitive information disclosure and
should be well considered.
'''
platforms = ["windows"]


[[permission.scope.deny]]
path = "$APPLOCALDATA/EBWebView/**"
```
 The above scopes can be used to allow access to the `APPLOCALDATA` folder, while preventing access to the `EBWebView` subfolder on windows, which contains sensitive webview data. These can merged into a set, which reduces duplicate configuration and makes it more understandable for anyone looking into the application configuration. First the deny scopes are merged into `deny-default`: plugins/fs/permissions/deny-default.toml 
```toml
[[set]]
identifier = "deny-default"
description = '''
This denies access to dangerous Tauri relevant files and
folders by default.
'''
permissions = ["deny-webview-data-linux", "deny-webview-data-windows"]
```
 Afterwards deny and allow scopes are merged: 
```toml
[[set]]
identifier = "scope-applocaldata-reasonable"
description = '''
This scope set allows access to the `APPLOCALDATA` folder and
subfolders except for linux,
while it denies access to dangerous Tauri relevant files and
folders by default on windows.
'''
permissions = ["scope-applocaldata-recursive", "deny-default"]
```
 These scopes can be either used for all commands, by extending the global scope of the plugin, or for only selected commands when they are used in combination with an enabled command inside a permission. Reasonable read only file access to files in the `APPLOCALDATA` could look like this: 
```toml
[[set]]
identifier = "read-files-applocaldata"
description = '''
This set allows file read access to the `APPLOCALDATA` folder and
subfolders except for linux,
while it denies access to dangerous Tauri relevant files and
folders by default on windows.'''
permissions = ["scope-applocaldata-reasonable", "allow-read-file"]
```
 These examples only highlight the scope functionality itself. Each plugin or application developer needs to consider reasonable combinations of scope depending on their use cases.