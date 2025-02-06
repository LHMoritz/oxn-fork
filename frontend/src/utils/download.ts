export const downloadFile = (fileData: Blob, filename: string) => {
  const url = window.URL.createObjectURL(fileData);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};
