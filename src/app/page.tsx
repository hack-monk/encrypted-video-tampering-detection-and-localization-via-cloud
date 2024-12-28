"use client";
import ChooseFile from "@/components/chooseFile";

export default function Home() {
  return (
    <div>
      <div className="m-10">
        <h1 className="text-black font-bold text-2xl text-center">
          Encrypted Video Tampering Detection and Localization through
          Cloud
        </h1>
        <p className="text-black text-center m-10">
          Upload a video file of your choice (mp4)
        </p>
      </div>
      <ChooseFile />
    </div>
  );
}
