// SC Salvage Tracker — AAA Setup Wizard (Launcher Polish · Inno Setup 6.7+)
// Farben entsprechen ui/themes/star_citizen.qss

#ifndef MyAppCodename
  #define MyAppCodename "Launcher Polish"
#endif

#ifndef MyAppBuild
  #define MyAppBuild "2026.06"
#endif

const
  TRACKER_BG = $12100A;
  TRACKER_PANEL = $271D15;
  TRACKER_INPUT = $30241A;
  TRACKER_TEXT = $F5EEE6;
  TRACKER_ORANGE = $2A7AE0;
  TRACKER_MUTED = $99A8B8;
  TRACKER_HINT = $8FA3B8;
  TRACKER_BTN_H = 32;
  TRACKER_BTN_GAP = 12;
  TRACKER_BTN_MARGIN = 24;
  TRACKER_BTN_W_NEXT = 136;
  TRACKER_BTN_W_CANCEL = 156;
  TRACKER_BTN_W_BACK = 136;
  TRACKER_BOTTOM_BAR_H = 56;
  TRACKER_CONTENT_PAD = 20;

function NewLine: String;
begin
  Result := Chr(13) + Chr(10);
end;

var
  TrackerBgImage: TBitmapImage;
  TrackerPanel: TPanel;
  TrackerAccentStripe: TPanel;
  TrackerBottomBar: TPanel;
  TrackerFooterLabel: TNewStaticText;

procedure WizardFormResized(Sender: TObject); forward;
procedure TrackerStyleInnerPages; forward;

procedure TrackerLockFont(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  L.StyleElements := L.StyleElements - [seFont];
end;

procedure TrackerStyleLabel(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  TrackerLockFont(L);
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 10;
  L.Font.Style := [fsBold];
  L.Font.Color := TRACKER_TEXT;
end;

procedure TrackerStyleTitle(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  TrackerLockFont(L);
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 15;
  L.Font.Style := [fsBold];
  L.Font.Color := TRACKER_ORANGE;
end;

procedure TrackerStyleMuted(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  TrackerLockFont(L);
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 9;
  L.Font.Style := [];
  L.Font.Color := TRACKER_MUTED;
end;

procedure TrackerStyleHint(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  TrackerLockFont(L);
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 9;
  L.Font.Style := [];
  L.Font.Color := TRACKER_HINT;
end;

procedure TrackerStyleInput(E: TNewEdit);
begin
  if E = nil then
    Exit;
  E.Font.Name := 'Segoe UI';
  E.Font.Size := 10;
end;

procedure TrackerStyleCheckList(L: TNewCheckListBox);
begin
  if L = nil then
    Exit;
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 10;
end;

procedure TrackerStyleMemo(M: TNewMemo);
begin
  if M = nil then
    Exit;
  M.Font.Name := 'Consolas';
  M.Font.Size := 9;
end;

procedure TrackerSyncDecorPanel;
begin
  if TrackerPanel <> nil then
  begin
    TrackerPanel.SetBounds(
      WizardForm.MainPanel.Left,
      WizardForm.MainPanel.Top,
      WizardForm.MainPanel.Width,
      WizardForm.MainPanel.Height);
  end;

  if TrackerAccentStripe <> nil then
  begin
    TrackerAccentStripe.SetBounds(
      WizardForm.MainPanel.Left,
      WizardForm.MainPanel.Top,
      ScaleX(4),
      WizardForm.MainPanel.Height);
  end;
end;

procedure TrackerLayoutPageHeaders;
var
  PadL, PadT, ContentW: Integer;
begin
  PadL := ScaleX(TRACKER_CONTENT_PAD);
  PadT := ScaleY(8);
  ContentW := WizardForm.MainPanel.Width - (PadL * 2);

  WizardForm.PageNameLabel.AutoSize := False;
  WizardForm.PageNameLabel.SetBounds(
    PadL, PadT, ContentW, ScaleY(28));

  WizardForm.PageDescriptionLabel.AutoSize := False;
  WizardForm.PageDescriptionLabel.SetBounds(
    PadL, PadT + ScaleY(30), ContentW, ScaleY(36));
end;

procedure TrackerLayoutWelcomePage;
var
  PadL, PadT, ContentW: Integer;
begin
  PadL := ScaleX(TRACKER_CONTENT_PAD);
  PadT := ScaleY(12);
  ContentW := WizardForm.WelcomePage.Width - (PadL * 2);

  WizardForm.WelcomeLabel1.AutoSize := False;
  WizardForm.WelcomeLabel1.SetBounds(
    PadL, PadT, ContentW, ScaleY(28));

  WizardForm.WelcomeLabel2.AutoSize := False;
  WizardForm.WelcomeLabel2.SetBounds(
    PadL, PadT + ScaleY(34), ContentW,
    WizardForm.WelcomePage.Height - PadT - ScaleY(40));
end;

procedure TrackerStyleInnerPages;
begin
  WizardForm.WizardSmallBitmapImage.Visible := False;

  WizardForm.SelectDirLabel.Caption :=
    'Der Salvage Tracker wird in folgenden Ordner installiert:';
  WizardForm.SelectDirBrowseLabel.Caption :=
    'Klicke auf Weiter, um fortzufahren — oder auf Durchsuchen, ' +
    'um einen anderen Ordner zu wählen.';
  WizardForm.DirBrowseButton.Caption := 'DURCHSUCHEN …';

  WizardForm.SelectDirLabel.Visible := True;
  WizardForm.SelectDirBrowseLabel.Visible := True;
  WizardForm.DirEdit.Visible := True;
  WizardForm.DirBrowseButton.Visible := True;
  WizardForm.DiskSpaceLabel.Visible := True;

  WizardForm.TasksList.Visible := True;
  WizardForm.ReadyLabel.Visible := True;
  WizardForm.ReadyMemo.Visible := True;
  WizardForm.StatusLabel.Visible := True;
  WizardForm.FilenameLabel.Visible := True;
end;

procedure TrackerApplyPageTheme;
begin
  WizardForm.Color := TRACKER_BG;
  WizardForm.MainPanel.Color := TRACKER_PANEL;
  WizardForm.InnerPage.Color := TRACKER_PANEL;
  WizardForm.WelcomePage.Color := TRACKER_PANEL;
  WizardForm.FinishedPage.Color := TRACKER_PANEL;

  if TrackerPanel <> nil then
    TrackerPanel.Color := TRACKER_PANEL;
  if TrackerAccentStripe <> nil then
    TrackerAccentStripe.Color := TRACKER_ORANGE;

  TrackerStyleTitle(WizardForm.WelcomeLabel1);
  TrackerStyleLabel(WizardForm.WelcomeLabel2);
  TrackerStyleTitle(WizardForm.FinishedLabel);
  TrackerStyleHint(WizardForm.PageDescriptionLabel);
  TrackerStyleTitle(WizardForm.PageNameLabel);

  TrackerStyleLabel(WizardForm.StatusLabel);
  TrackerStyleHint(WizardForm.FilenameLabel);
  TrackerStyleLabel(WizardForm.SelectDirLabel);
  TrackerStyleHint(WizardForm.SelectDirBrowseLabel);
  TrackerStyleLabel(WizardForm.SelectStartMenuFolderLabel);
  TrackerStyleLabel(WizardForm.SelectComponentsLabel);
  TrackerStyleHint(WizardForm.SelectTasksLabel);
  TrackerStyleLabel(WizardForm.ReadyLabel);
  TrackerStyleLabel(WizardForm.PreparingLabel);
  TrackerStyleMuted(WizardForm.DiskSpaceLabel);

  TrackerStyleInput(WizardForm.DirEdit);
  TrackerStyleCheckList(WizardForm.TasksList);
  TrackerStyleMemo(WizardForm.ReadyMemo);

  WizardForm.BackButton.Caption := '◂ ZURÜCK';
  WizardForm.NextButton.Caption := 'WEITER ▸';
  WizardForm.CancelButton.Caption := 'ABBRECHEN';

  WizardForm.WizardBitmapImage.Visible := False;
  WizardForm.WizardSmallBitmapImage.Visible := False;
  WizardForm.BeveledLabel.Visible := False;

  TrackerStyleInnerPages;

  if TrackerFooterLabel <> nil then
  begin
    TrackerFooterLabel.Caption :=
      ExpandConstant('{#MyAppCodename}') + ' · Build ' +
      ExpandConstant('{#MyAppBuild}') +
      ' · SC Salvage Tracker Setup';
    TrackerStyleMuted(TrackerFooterLabel);
  end;
end;

procedure TrackerLayoutButtons;
var
  TopPos, RightPos: Integer;
begin
  TopPos := WizardForm.ClientHeight - TRACKER_BOTTOM_BAR_H +
    ((TRACKER_BOTTOM_BAR_H - TRACKER_BTN_H) div 2);

  RightPos := WizardForm.ClientWidth - TRACKER_BTN_MARGIN;
  WizardForm.CancelButton.SetBounds(
    RightPos - TRACKER_BTN_W_CANCEL, TopPos,
    TRACKER_BTN_W_CANCEL, TRACKER_BTN_H);

  RightPos := RightPos - TRACKER_BTN_W_CANCEL - TRACKER_BTN_GAP;
  WizardForm.NextButton.SetBounds(
    RightPos - TRACKER_BTN_W_NEXT, TopPos,
    TRACKER_BTN_W_NEXT, TRACKER_BTN_H);

  if WizardForm.BackButton.Visible then
  begin
    RightPos := RightPos - TRACKER_BTN_W_NEXT - TRACKER_BTN_GAP;
    WizardForm.BackButton.SetBounds(
      RightPos - TRACKER_BTN_W_BACK, TopPos,
      TRACKER_BTN_W_BACK, TRACKER_BTN_H);
  end;

  if TrackerBottomBar <> nil then
    TrackerBottomBar.BringToFront;

  WizardForm.BackButton.BringToFront;
  WizardForm.NextButton.BringToFront;
  WizardForm.CancelButton.BringToFront;
end;

procedure TrackerLayoutWizard;
begin
  if TrackerBgImage <> nil then
  begin
    TrackerBgImage.SetBounds(
      0, 0, WizardForm.ClientWidth, WizardForm.ClientHeight);
    TrackerBgImage.SendToBack;
  end;

  TrackerSyncDecorPanel;

  if WizardForm.CurPageID = wpWelcome then
    TrackerLayoutWelcomePage
  else if WizardForm.CurPageID <> wpFinished then
    TrackerLayoutPageHeaders;

  if TrackerPanel <> nil then
    TrackerPanel.SendToBack;

  if TrackerAccentStripe <> nil then
    TrackerAccentStripe.BringToFront;

  WizardForm.MainPanel.BringToFront;

  if TrackerFooterLabel <> nil then
  begin
    TrackerFooterLabel.SetBounds(
      24,
      WizardForm.ClientHeight - TRACKER_BOTTOM_BAR_H +
        ((TRACKER_BOTTOM_BAR_H - 18) div 2),
      460, 18);
    TrackerFooterLabel.BringToFront;
  end;

  if TrackerBottomBar <> nil then
  begin
    TrackerBottomBar.SetBounds(
      0, WizardForm.ClientHeight - TRACKER_BOTTOM_BAR_H,
      WizardForm.ClientWidth, TRACKER_BOTTOM_BAR_H);
    TrackerBottomBar.SendToBack;
  end;

  TrackerLayoutButtons;
end;

procedure TrackerUpdateHeader;
begin
  case WizardForm.CurPageID of
    wpWelcome:
      begin
        WizardForm.WelcomeLabel1.Caption :=
          '◆ SC SALVAGE TRACKER · SETUP';
        WizardForm.WelcomeLabel2.Caption :=
          'Willkommen beim Installationsassistenten.' + NewLine + NewLine +
          'Version ' + ExpandConstant('{#MyAppVersion}') +
          ' · Build ' + ExpandConstant('{#MyAppBuild}') + NewLine +
          ExpandConstant('{#MyAppCodename}') + NewLine + NewLine +
          'Dieser Assistent installiert den Salvage Tracker mit ' +
          'Sitzungen, Raffinerie, Verkäufen, Lager und Crew-Auszahlung.' +
          NewLine + NewLine +
          'Klicke auf Weiter, um fortzufahren.';
      end;
    wpSelectDir:
      begin
        WizardForm.PageNameLabel.Caption := '◆ INSTALLATIONSORDNER';
        WizardForm.PageDescriptionLabel.Caption :=
          'Wähle den Zielordner für den Salvage Tracker.';
      end;
    wpSelectTasks:
      begin
        WizardForm.PageNameLabel.Caption := '◆ ZUSÄTZLICHE OPTIONEN';
        WizardForm.PageDescriptionLabel.Caption :=
          'Desktop-Verknüpfung und Start nach der Installation.';
      end;
    wpReady:
      begin
        WizardForm.PageNameLabel.Caption := '◆ BEREIT ZUR INSTALLATION';
        WizardForm.PageDescriptionLabel.Caption :=
          'Alle Einstellungen sind gewählt. Klicke auf Installieren.';
      end;
    wpInstalling:
      begin
        WizardForm.PageNameLabel.Caption := '◆ INSTALLATION LÄUFT';
        WizardForm.PageDescriptionLabel.Caption :=
          'Dateien werden entpackt — bitte warten …';
      end;
    wpFinished:
      begin
        WizardForm.FinishedLabel.Caption :=
          '◆ INSTALLATION ABGESCHLOSSEN' + NewLine + NewLine +
          'Der Salvage Tracker wurde erfolgreich installiert.' + NewLine +
          'Starte die Anwendung über das Startmenü oder die Desktop-Verknüpfung.';
      end;
  end;
end;

function InitializeSetup(): Boolean;
begin
  ExtractTemporaryFile('install_bg.png');
  Result := True;
end;

procedure InitializeWizard();
begin
  WizardForm.ClientWidth := ScaleX(920);
  WizardForm.ClientHeight := ScaleY(580);
  WizardForm.Position := poScreenCenter;

  TrackerBgImage := TBitmapImage.Create(WizardForm);
  TrackerBgImage.Parent := WizardForm;
  TrackerBgImage.Stretch := True;
  TrackerBgImage.AutoSize := False;
  TrackerBgImage.BackColor := TRACKER_BG;
  try
    TrackerBgImage.Bitmap.LoadFromFile(
      ExpandConstant('{tmp}\install_bg.png'));
  except
    TrackerBgImage.Visible := False;
  end;

  TrackerPanel := TPanel.Create(WizardForm);
  TrackerPanel.Parent := WizardForm;
  TrackerPanel.Color := TRACKER_PANEL;
  TrackerPanel.BevelOuter := bvNone;
  TrackerPanel.BevelInner := bvNone;

  TrackerAccentStripe := TPanel.Create(WizardForm);
  TrackerAccentStripe.Parent := WizardForm;
  TrackerAccentStripe.Color := TRACKER_ORANGE;
  TrackerAccentStripe.BevelOuter := bvNone;
  TrackerAccentStripe.BevelInner := bvNone;

  TrackerBottomBar := TPanel.Create(WizardForm);
  TrackerBottomBar.Parent := WizardForm;
  TrackerBottomBar.Color := TRACKER_BG;
  TrackerBottomBar.BevelOuter := bvNone;
  TrackerBottomBar.BevelInner := bvNone;

  TrackerFooterLabel := TNewStaticText.Create(WizardForm);
  TrackerFooterLabel.Parent := WizardForm;
  TrackerFooterLabel.AutoSize := False;

  TrackerApplyPageTheme();
  TrackerLayoutWizard();
  TrackerUpdateHeader();

  WizardForm.OnResize := @WizardFormResized;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  TrackerApplyPageTheme();
  TrackerUpdateHeader();
  TrackerLayoutWizard();

  if CurPageID = wpReady then
    WizardForm.NextButton.Caption := 'INSTALLIEREN ▸'
  else if CurPageID = wpFinished then
    WizardForm.NextButton.Caption := 'FERTIGSTELLEN'
  else if CurPageID <> wpInstalling then
    WizardForm.NextButton.Caption := 'WEITER ▸';

  TrackerLayoutButtons;
end;

procedure WizardFormResized(Sender: TObject);
begin
  TrackerLayoutWizard();
  TrackerApplyPageTheme();
end;

procedure DeinitializeWizard();
begin
  TrackerBgImage := nil;
  TrackerPanel := nil;
  TrackerAccentStripe := nil;
  TrackerBottomBar := nil;
  TrackerFooterLabel := nil;
end;
