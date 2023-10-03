"use client";
import React from "react";
import { IconButton, Input, InputAdornment } from "@mui/material";
import { useSearchParams } from "next/navigation";

import { useForm, Controller } from "react-hook-form";
import { Confirm } from "@/components/join/confirm";
import { Layout } from "@/components/join/layout";
import { ChevronRight } from "@mui/icons-material";

type FormValues = {
  flakeUrl: string;
};

export default function JoinPrequel() {
  const queryParams = useSearchParams();
  const flakeUrl = queryParams.get("flake") || "";
  const flakeAttr = queryParams.get("attr") || "default";
  const { handleSubmit, control, formState, getValues, reset } =
    useForm<FormValues>({ defaultValues: { flakeUrl: "" } });

  return (
    <Layout>
      {!formState.isSubmitted && !flakeUrl && (
        <form
          onSubmit={handleSubmit(() => {})}
          className="w-full max-w-2xl justify-self-center"
        >
          <Controller
            name="flakeUrl"
            control={control}
            render={({ field }) => (
              <Input
                color="secondary"
                aria-required="true"
                {...field}
                required
                fullWidth
                startAdornment={
                  <InputAdornment position="start">Clan</InputAdornment>
                }
                endAdornment={
                  <InputAdornment position="end">
                    <IconButton type="submit">
                      <ChevronRight />
                    </IconButton>
                  </InputAdornment>
                }
              />
            )}
          />
        </form>
      )}
      {(formState.isSubmitted || flakeUrl) && (
        <Confirm
          handleBack={() => reset()}
          flakeUrl={formState.isSubmitted ? getValues("flakeUrl") : flakeUrl}
          flakeAttr={flakeAttr}
        />
      )}
    </Layout>
  );
}