require('@testing-library/jest-dom');

// Polyfill TextEncoder/TextDecoder, which jsdom does not provide (undici needs them too).
const { TextEncoder, TextDecoder } = require('util');
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// jsdom does not ship the WHATWG fetch primitives that React Router's loader/action
// navigation relies on. Polyfill them with undici (the same implementation Node uses),
// after providing the web globals undici itself depends on.
const { ReadableStream, WritableStream, TransformStream } = require('node:stream/web');
const { MessageChannel, MessagePort } = require('node:worker_threads');
const { Blob } = require('node:buffer');
Object.assign(global, { ReadableStream, WritableStream, TransformStream, MessageChannel, MessagePort, Blob });
const { fetch, Request, Response, Headers, FormData } = require('undici');
Object.assign(global, { fetch, Request, Response, Headers, FormData });

// jsdom does not implement these layout methods.
Element.prototype.scrollIntoView = jest.fn();
Element.prototype.scrollTo = jest.fn();
window.scrollTo = jest.fn();
