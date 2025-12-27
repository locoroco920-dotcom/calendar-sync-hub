/// <reference types="vite/client" />

declare module 'ical.js' {
  export function parse(input: string): any;
  export class Component {
    constructor(jCal: any);
    getAllSubcomponents(name: string): Component[];
    getFirstPropertyValue(name: string): any;
  }
  export class Event {
    constructor(component: Component);
    uid: string;
    summary: string;
    description: string;
    location: string;
    startDate: Time;
    endDate: Time;
  }
  export class Time {
    toJSDate(): Date;
  }
}
