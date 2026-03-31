const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function withBasePath(path: string) {
  if (
    path.startsWith("http://") ||
    path.startsWith("https://") ||
    path.startsWith("data:") ||
    path.startsWith("#")
  ) {
    return path;
  }

  return `${BASE_PATH}${path.startsWith("/") ? path : `/${path}`}`;
}
