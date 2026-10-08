/** A file as a folder selection gives it, with the chosen folder in front. */
export function folderFile(path: string, content: BlobPart = "x"): File {
  const file = new File([content], path.split("/").at(-1)!);
  Object.defineProperty(file, "webkitRelativePath", { value: `mybot/${path}` });
  return file;
}
