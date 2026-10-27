import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { UploadResult } from "@/lib/resumes";

import { ResumeUploadForm } from "./ResumeUploadForm";

const resume = {
  id: "r-1",
  original_filename: "cv.pdf",
  content_type: "application/pdf",
  size_bytes: 8,
  uploaded_at: "2026-10-27T18:00:00Z",
};

function setup(result: UploadResult = { state: "ok", resume }) {
  const upload = vi.fn().mockResolvedValue(result);
  const onUploaded = vi.fn();
  render(<ResumeUploadForm upload={upload} onUploaded={onUploaded} />);
  return { upload, onUploaded };
}

function chooseFile(name = "cv.pdf", content = "%PDF-1.7") {
  const file = new File([content], name);
  fireEvent.change(screen.getByLabelText(/Arquivo/), { target: { files: [file] } });
  return file;
}

const consentBox = () => screen.getByRole("checkbox");
const sendButton = () => screen.getByRole("button", { name: "Enviar currículo" });

describe("ResumeUploadForm", () => {
  it("só libera o envio com arquivo e consentimento", () => {
    setup();
    expect(sendButton()).toBeDisabled();

    chooseFile();
    expect(sendButton()).toBeDisabled();

    fireEvent.click(consentBox());
    expect(sendButton()).toBeEnabled();
  });

  it("mostra o termo de consentimento", () => {
    setup();

    expect(screen.getByText(/Autorizo o Job Finder a guardar meu currículo/)).toBeInTheDocument();
  });

  it("envia o arquivo e avisa a página", async () => {
    const { upload, onUploaded } = setup();
    const file = chooseFile();
    fireEvent.click(consentBox());

    fireEvent.click(sendButton());

    await waitFor(() => expect(onUploaded).toHaveBeenCalledWith(resume));
    expect(upload).toHaveBeenCalledWith(file);
    expect(screen.getByRole("status")).toHaveTextContent('Currículo "cv.pdf" enviado!');
  });

  it("avisa na hora quando o formato não é aceito", () => {
    setup();

    chooseFile("foto.png");
    fireEvent.click(consentBox());

    expect(screen.getByRole("alert")).toHaveTextContent("Envie o currículo em PDF ou DOCX.");
    expect(sendButton()).toBeDisabled();
  });

  it("mostra o erro devolvido pela API", async () => {
    const { onUploaded } = setup({ state: "error", message: "O arquivo passa de 5 MB." });
    chooseFile();
    fireEvent.click(consentBox());

    fireEvent.click(sendButton());

    expect(await screen.findByRole("alert")).toHaveTextContent("O arquivo passa de 5 MB.");
    expect(onUploaded).not.toHaveBeenCalled();
  });
});

describe("ResumeUploadForm com aviso", () => {
  it("mostra o aviso devolvido junto com o envio", async () => {
    setup({ state: "ok", resume, notice: "Currículo enviado, mas a análise não deu certo." });
    chooseFile();
    fireEvent.click(consentBox());

    fireEvent.click(sendButton());

    expect(await screen.findByRole("status")).toHaveTextContent("a análise não deu certo");
  });
});
