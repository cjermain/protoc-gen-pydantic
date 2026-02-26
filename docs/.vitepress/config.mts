import { defineConfig } from "vitepress";

export default defineConfig({
  title: "protoc-gen-pydantic",
  description:
    "A protoc plugin that generates Pydantic v2 models from .proto files",
  base: "/protoc-gen-pydantic/",

  head: [
    [
      "link",
      { rel: "icon", href: "/protoc-gen-pydantic/favicon.ico", sizes: "any" },
    ],
    [
      "link",
      {
        rel: "icon",
        href: "/protoc-gen-pydantic/favicon-32x32.png",
        type: "image/png",
        sizes: "32x32",
      },
    ],
    [
      "link",
      {
        rel: "icon",
        href: "/protoc-gen-pydantic/favicon-16x16.png",
        type: "image/png",
        sizes: "16x16",
      },
    ],
    [
      "link",
      {
        rel: "apple-touch-icon",
        href: "/protoc-gen-pydantic/apple-touch-icon.png",
        sizes: "180x180",
      },
    ],
    [
      "link",
      {
        rel: "manifest",
        href: "/protoc-gen-pydantic/site.webmanifest",
      },
    ],
  ],

  themeConfig: {
    nav: [
      { text: "Guide", link: "/guide/installation" },
      { text: "Features", link: "/features/field-types" },
      { text: "Options", link: "/options" },
      { text: "buf.validate", link: "/buf-validate" },
      {
        text: "GitHub",
        link: "https://github.com/cjermain/protoc-gen-pydantic",
      },
    ],

    sidebar: [
      {
        text: "Getting Started",
        items: [
          { text: "Installation", link: "/guide/installation" },
          { text: "Quickstart", link: "/guide/quickstart" },
          { text: "Using with protoc", link: "/guide/with-protoc" },
          { text: "Using with buf", link: "/guide/with-buf" },
        ],
      },
      {
        text: "Features",
        items: [
          { text: "Field Types", link: "/features/field-types" },
          { text: "Well-Known Types", link: "/features/well-known-types" },
          { text: "Nested Types", link: "/features/nested-types" },
          { text: "Enums", link: "/features/enums" },
          { text: "Comments & Descriptions", link: "/features/comments" },
          { text: "Reserved Names", link: "/features/reserved-names" },
        ],
      },
      {
        text: "Reference",
        items: [
          { text: "Plugin Options", link: "/options" },
          { text: "buf.validate", link: "/buf-validate" },
        ],
      },
      {
        text: "Contributing",
        link: "/contributing",
      },
    ],

    search: {
      provider: "local",
    },

    socialLinks: [
      {
        icon: "github",
        link: "https://github.com/cjermain/protoc-gen-pydantic",
      },
    ],

    editLink: {
      pattern:
        "https://github.com/cjermain/protoc-gen-pydantic/edit/main/docs/:path",
      text: "Edit this page on GitHub",
    },

    footer: {
      message: "Released under the Apache 2.0 License.",
      copyright: "Copyright © 2024–present protoc-gen-pydantic contributors",
    },
  },
});
