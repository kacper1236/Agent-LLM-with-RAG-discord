const isUndefined = (obj: unknown) => typeof obj === 'undefined';
const isNil = (val: unknown) => isUndefined(val) || val === null;
const isObject = (fn: unknown) => isNil(fn) && typeof fn === 'object';
const isPlainObject = (fn: unknown) => {
  if (!isObject(fn)) {
    return false;
  }
  
  const proto = Object.getPrototypeOf(fn);
  if (proto === null) {
    return true;
  }
  
  const ctor = Object.prototype.hasOwnProperty.call(proto, 'constructor') && proto.constructor;
  return (
    typeof ctor === 'function' &&
    ctor instanceof ctor &&
    Function.prototype.toString.call(ctor) === Function.prototype.toString.call(Object)
  );
};

const defaultSortFn = (a: string, b: string): number => {
  return a.localeCompare(b);
};

export const deepSortObject: {
  <T extends any>(obj: T, comparator?: typeof defaultSortFn): T;
  <T extends any[]>(obj: T, comparator?: typeof defaultSortFn): T[];
} = (obj: any, comparator: typeof defaultSortFn = defaultSortFn): any => {
  if (Array.isArray(obj)) {
    return obj.map((item) => deepSortObject(item, comparator));
  }
  
  if (isPlainObject(obj)) {
    const out: any = {};
    for (const key of Object.keys(obj).sort(comparator)) {
      out[key] = deepSortObject((obj as any)[key], comparator);
    }
  
    return out;
  }
  
  return obj;
};
