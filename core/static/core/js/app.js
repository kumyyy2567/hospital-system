document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initSupportDrawer();
  highlightActiveNav();
  initDismissibleAlerts();
  initRevealCards();
  initInteractiveSurfaces();
  initMetricCounters();
  initChatWidgets();
  initHomeLanding();
  initTableFilters();
  initBookingPreview();
  initAdminChart();
  initLiveDashboardStats();
  initLiveNotifications();
  initAppointmentActions();
  scrollChatsToBottom();
});

function initNavigation() {
  const toggle = document.querySelector('[data-nav-toggle]');
  const menu = document.querySelector('[data-nav-menu]');

  if (!toggle || !menu) {
    return;
  }

  toggle.addEventListener('click', () => {
    toggle.classList.toggle('is-open');
    menu.classList.toggle('is-open');
  });
}

function initSupportDrawer() {
  const drawer = document.querySelector('[data-support-drawer]');
  const openButton = document.querySelector('[data-support-toggle]');
  const closeButton = document.querySelector('[data-support-close]');

  if (!drawer || !openButton || !closeButton) {
    return;
  }

  openButton.addEventListener('click', () => drawer.classList.add('is-open'));
  closeButton.addEventListener('click', () => drawer.classList.remove('is-open'));

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      drawer.classList.remove('is-open');
    }
  });
}

function highlightActiveNav() {
  document.querySelectorAll('.nav-links a').forEach((link) => {
    if (window.location.pathname === link.getAttribute('href')) {
      link.style.background = '#e6f7f5';
      link.style.borderColor = '#c2e5df';
      link.style.color = '#0f766e';
    }
  });
}

function initDismissibleAlerts() {
  document.querySelectorAll('[data-alert-close]').forEach((button) => {
    button.addEventListener('click', () => hideAlert(button.closest('[data-alert]')));
  });
}

function initRevealCards() {
  const cards = document.querySelectorAll('.card.reveal');
  if (!cards.length || typeof IntersectionObserver === 'undefined') {
    cards.forEach((card) => card.classList.add('in-view'));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  cards.forEach((card) => observer.observe(card));
}

function initInteractiveSurfaces() {
  const surfaces = Array.from(document.querySelectorAll('[data-spotlight]'));
  if (!surfaces.length) {
    return;
  }

  surfaces.forEach((surface, index) => {
    if (surface.dataset.spotlightReady === 'true') {
      return;
    }
    surface.dataset.spotlightReady = 'true';
    surface.style.setProperty('--surface-delay', `${Math.min(index * 35, 210)}ms`);

    surface.addEventListener('pointermove', (event) => {
      const rect = surface.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      surface.style.setProperty('--spotlight-x', `${x}px`);
      surface.style.setProperty('--spotlight-y', `${y}px`);
      surface.classList.add('is-spotlight-active');
    });

    surface.addEventListener('pointerleave', () => {
      surface.classList.remove('is-spotlight-active');
    });
  });
}

function initMetricCounters() {
  document.querySelectorAll('[data-count]').forEach((element) => {
    animateMetricValue(element, Number(element.dataset.count || '0'));
  });
}

function initChatWidgets() {
  document.querySelectorAll('[data-chat-widget]').forEach((widget) => {
    const input = widget.querySelector('[data-chat-input]');
    const send = widget.querySelector('[data-chat-send]');
    const messages = widget.querySelector('[data-chat-messages]');
    const typing = widget.querySelector('[data-chat-typing]');
    const replies = (widget.dataset.replies || '').split('|').filter(Boolean);

    if (!input || !send || !messages) {
      return;
    }

    const submitMessage = () => {
      const text = input.value.trim();
      if (!text) {
        return;
      }

      appendChatMessage(messages, text, true);
      input.value = '';
      messages.scrollTop = messages.scrollHeight;

      if (typing) {
        typing.classList.add('is-visible');
      }

      window.setTimeout(() => {
        const reply = replies.length
          ? replies[Math.floor(Math.random() * replies.length)]
          : 'Thanks, your request has been noted.';
        appendChatMessage(messages, reply, false);
        if (typing) {
          typing.classList.remove('is-visible');
        }
        messages.scrollTop = messages.scrollHeight;
      }, 650);
    };

    send.addEventListener('click', submitMessage);
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        submitMessage();
      }
    });
  });
}

function initHomeLanding() {
  const shell = document.querySelector('.home-shell');
  if (!shell) {
    return;
  }

  const liveUrl = shell.dataset.homeLiveUrl;
  const doctorsUrl = shell.dataset.homeDoctorsUrl;
  const callbackUrl = shell.dataset.callbackUrl;
  const patientBookUrl = shell.dataset.patientBookUrl || '';
  const signupUrl = shell.dataset.signupUrl || '';
  const canBook = shell.dataset.canBook === 'true';
  const callbackForm = shell.querySelector('[data-callback-form]');
  const callbackFeedback = shell.querySelector('[data-callback-feedback]');
  const homeStatElements = shell.querySelectorAll('[data-home-stat-key]');
  const specialtyCards = Array.from(shell.querySelectorAll('[data-home-specialty]'));
  const specialtyDots = Array.from(shell.querySelectorAll('[data-specialty-dot]'));
  const filterButtons = Array.from(shell.querySelectorAll('[data-directory-specialty]'));
  const directory = shell.querySelector('[data-home-directory]');
  let activeSpecialty = 'ALL';
  let rotateIndex = 0;

  const setActiveSpecialtyVisual = (index) => {
    specialtyCards.forEach((card, cardIndex) => card.classList.toggle('is-active', cardIndex === index));
    specialtyDots.forEach((dot, dotIndex) => dot.classList.toggle('is-active', dotIndex === index));
  };

  const syncDirectoryFilter = (specialtyName) => {
    activeSpecialty = specialtyName || 'ALL';
    filterButtons.forEach((button) => {
      button.classList.toggle('is-active', button.dataset.directorySpecialty === activeSpecialty);
    });
  };

  const renderDirectory = (doctors) => {
    if (!directory) {
      return;
    }

    if (!doctors.length) {
      directory.innerHTML = '<div class="notification-empty">No doctors found for this speciality yet.</div>';
      return;
    }

    directory.innerHTML = doctors
      .map(
        (doctor) => `
          <article class="doctor-directory-card" data-spotlight>
            <div class="doctor-directory-head">
              <div class="doctor-avatar">${escapeHtml(doctor.name.slice(0, 2).toUpperCase())}</div>
              <div>
                <h3>${escapeHtml(doctor.name)}</h3>
                <p>${escapeHtml(`${doctor.specialization} • ${doctor.location || 'Main Hospital'}`)}</p>
              </div>
            </div>
            <div class="doctor-directory-meta">
              <span>Experience</span>
              <strong>${escapeHtml(doctor.experience_label || 'Consultant available')}</strong>
            </div>
            <div class="doctor-directory-meta">
              <span>Fee</span>
              <strong>Rs. ${Math.round(Number(doctor.fee || 0))}</strong>
            </div>
            <div class="doctor-directory-meta">
              <span>Open Slots</span>
              <strong>${escapeHtml(String(doctor.open_slots))}</strong>
            </div>
            <div class="doctor-directory-meta">
              <span>Next Slot</span>
              <strong>${escapeHtml(doctor.next_slot)}</strong>
            </div>
            <div class="doctor-directory-actions">
              <a class="btn" href="${escapeHtml(canBook ? `${patientBookUrl}?doctor=${doctor.id}` : signupUrl)}">Book Now</a>
            </div>
          </article>
        `
      )
      .join('');
    initInteractiveSurfaces();
  };

  const refreshHomeStats = async () => {
    if (!liveUrl) {
      return;
    }

    try {
      const data = await requestJSON(liveUrl);
      homeStatElements.forEach((element) => {
        const key = element.dataset.homeStatKey;
        if (key in data) {
          element.textContent = data[key];
        }
      });

      if (Array.isArray(data.specialties)) {
        specialtyCards.forEach((card) => {
          const name = card.dataset.specialtyName;
          const summary = data.specialties.find((item) => item.name === name);
          const countLabel = card.querySelector('span');
          if (summary && countLabel) {
            countLabel.textContent = `${summary.total_doctors} doctors`;
          }
        });
      }
    } catch (error) {
      // Retry on next interval.
    }
  };

  const loadDirectory = async (specialty) => {
    if (!doctorsUrl) {
      return;
    }

    try {
      const query = specialty && specialty !== 'ALL' ? `?specialty=${encodeURIComponent(specialty)}` : '';
      const data = await requestJSON(`${doctorsUrl}${query}`);
      renderDirectory(data.doctors || []);
    } catch (error) {
      showTransientAlert('Unable to refresh the live doctor directory right now.', 'error');
    }
  };

  if (callbackForm && callbackUrl) {
    callbackForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const submitButton = callbackForm.querySelector('button[type="submit"]');
      setButtonLoading(submitButton, true);
      callbackFeedback.textContent = 'Submitting your request...';

      try {
        const data = await requestJSON(callbackUrl, {
          method: 'POST',
          body: new FormData(callbackForm),
        });
        callbackForm.reset();
        callbackFeedback.textContent = data.message || 'Request submitted successfully.';
        showTransientAlert('Callback request submitted successfully.');
        refreshHomeStats();
      } catch (error) {
        callbackFeedback.textContent = 'Please check your details and try again.';
        showTransientAlert('Unable to submit the callback request right now.', 'error');
      } finally {
        setButtonLoading(submitButton, false);
      }
    });
  }

  specialtyCards.forEach((card, index) => {
    card.addEventListener('click', () => {
      rotateIndex = index;
      setActiveSpecialtyVisual(index);
      syncDirectoryFilter(card.dataset.specialtyName);
      loadDirectory(card.dataset.specialtyName);
    });
  });

  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const specialty = button.dataset.directorySpecialty || 'ALL';
      syncDirectoryFilter(specialty);
      loadDirectory(specialty);
    });
  });

  if (specialtyCards.length) {
    window.setInterval(() => {
      rotateIndex = (rotateIndex + 1) % specialtyCards.length;
      setActiveSpecialtyVisual(rotateIndex);
    }, 3200);
  }

  refreshHomeStats();
  loadDirectory(activeSpecialty);
  window.setInterval(refreshHomeStats, 20000);
}

function initTableFilters() {
  document.querySelectorAll('[data-table-shell]').forEach((shell) => {
    const rows = Array.from(shell.querySelectorAll('[data-row-search]'));
    const searchInput = shell.querySelector('[data-table-search]');
    const chips = Array.from(shell.querySelectorAll('[data-status-filter]'));
    let activeStatus = 'ALL';

    const applyFilters = () => {
      const query = (searchInput?.value || '').trim().toLowerCase();

      rows.forEach((row) => {
        const rowSearch = (row.dataset.rowSearch || '').toLowerCase();
        const rowStatus = (row.dataset.status || 'ALL').toUpperCase();
        const queryMatch = !query || rowSearch.includes(query);
        const statusMatch = activeStatus === 'ALL' || rowStatus === activeStatus;
        row.classList.toggle('is-hidden', !(queryMatch && statusMatch));
      });
    };

    if (searchInput) {
      searchInput.addEventListener('input', applyFilters);
    }

    chips.forEach((chip) => {
      chip.addEventListener('click', () => {
        activeStatus = chip.dataset.statusFilter || 'ALL';
        chips.forEach((item) => item.classList.remove('is-active'));
        chip.classList.add('is-active');
        applyFilters();
      });
    });

    applyFilters();
  });
}

function initBookingPreview() {
  const shell = document.querySelector('[data-booking-shell]');
  if (!shell) {
    return;
  }
  shell.classList.add('is-enhanced');

  const bookingForm = shell.querySelector('form.booking-form');
  const doctorField = shell.querySelector('select[name="doctor"]');
  const slotField = shell.querySelector('select[name="slot"]');
  const paymentField = shell.querySelector('select[name="payment_method"]');
  const gmailField = shell.querySelector('input[name="gmail"]');
  const doctorCards = Array.from(shell.querySelectorAll('[data-doctor-card]'));
  const paymentOptions = Array.from(shell.querySelectorAll('[data-payment-option]'));
  const doctorSearch = shell.querySelector('[data-booking-doctor-search]');
  const doctorSearchCount = shell.querySelector('[data-booking-search-count]');
  const doctorEmptyState = shell.querySelector('[data-booking-doctor-empty]');
  const slotOptions = shell.querySelector('[data-slot-options]');
  const slotSummary = shell.querySelector('[data-slot-summary]');
  const slotFilterButtons = Array.from(shell.querySelectorAll('[data-slot-filter]'));
  const slotSyncNote = shell.querySelector('[data-slot-sync-note]');
  const paymentFeedback = shell.querySelector('[data-payment-feedback]');
  const upiPanel = shell.querySelector('[data-upi-panel]');
  const upiLink = shell.querySelector('[data-upi-link]');
  const upiAmount = shell.querySelector('[data-upi-amount]');
  const upiIdTrigger = shell.querySelector('[data-upi-id-trigger]');
  const copyUpiButton = shell.querySelector('[data-copy-upi]');
  const showUpiQrButton = shell.querySelector('[data-show-upi-qr]');
  const gmailFeedback = shell.querySelector('[data-gmail-feedback]');
  const submitButton = shell.querySelector('[data-booking-submit]');
  const doctorPreview = shell.querySelector('[data-preview-doctor]');
  const locationPreview = shell.querySelector('[data-preview-location]');
  const specializationPreview = shell.querySelector('[data-preview-specialization]');
  const experiencePreview = shell.querySelector('[data-preview-experience]');
  const feePreview = shell.querySelector('[data-preview-fee]');
  const platformFeePreview = shell.querySelector('[data-preview-platform-fee]');
  const totalPreview = shell.querySelector('[data-preview-total]');
  const nextPreview = shell.querySelector('[data-preview-next]');
  const openSlotsPreview = shell.querySelector('[data-preview-open-slots]');
  const slotPreview = shell.querySelector('[data-preview-slot]');
  const gmailPreview = shell.querySelector('[data-preview-gmail]');
  const paymentMethodPreview = shell.querySelector('[data-preview-payment-method]');
  const paymentStatusPreview = shell.querySelector('[data-preview-payment-status]');
  const readinessPreview = shell.querySelector('[data-preview-readiness]');
  const previewNote = shell.querySelector('[data-preview-note]');
  const consultationBreakdown = shell.querySelector('[data-breakdown-consultation-fee]');
  const platformBreakdown = shell.querySelector('[data-breakdown-platform-fee]');
  const totalBreakdown = shell.querySelector('[data-breakdown-total]');
  const steps = Array.from(document.querySelectorAll('[data-progress-step]'));
  const slotsUrlTemplate = shell.dataset.slotsUrlTemplate || '';
  const bookingPlatformFee = Number(shell.dataset.bookingPlatformFee || '0');
  const hospitalUpiId = shell.dataset.hospitalUpiId || '';
  const hospitalUpiPayee = shell.dataset.hospitalUpiPayee || 'Hospital Appointment Desk';
  const upiModal = document.querySelector('[data-upi-modal]');
  const upiQrImage = document.querySelector('[data-upi-qr-image]');
  const upiModalLink = document.querySelector('[data-upi-modal-link]');
  const upiModalDoctor = document.querySelector('[data-upi-modal-doctor]');
  const upiModalSlot = document.querySelector('[data-upi-modal-slot]');
  const upiModalTotal = document.querySelector('[data-upi-modal-total]');
  const upiModalId = document.querySelector('[data-upi-modal-id]');
  const upiConfirmButton = document.querySelector('[data-upi-confirm]');
  const upiCloseButtons = Array.from(document.querySelectorAll('[data-upi-close]'));
  let selectedSlotMeta = null;
  let loadedSlots = [];
  let activeSlotFilter = 'ALL';
  let slotRequestId = 0;
  let allowUpiSubmit = false;

  if (!doctorField || !slotField || !paymentField || !gmailField) {
    return;
  }

  const getSelectedDoctorCard = () =>
    doctorCards.find((card) => String(card.dataset.doctorId) === String(doctorField.value));

  const getPaymentTitle = (value) => {
    const activeOption = paymentOptions.find((option) => option.dataset.paymentValue === value);
    if (activeOption) {
      return activeOption.dataset.paymentTitle || activeOption.dataset.paymentValue || 'Not selected';
    }
    if (value === 'PAY_AT_HOSPITAL') {
      return 'Pay at Hospital';
    }
    if (value === 'NET_BANKING') {
      return 'Net Banking';
    }
    if (value === 'CARD') {
      return 'Card';
    }
    if (value === 'UPI') {
      return 'UPI';
    }
    return 'Not selected';
  };

  const buildUpiUri = () => {
    const selectedDoctor = getSelectedDoctorCard();
    const consultationFee = selectedDoctor ? Math.round(Number(selectedDoctor.dataset.fee || '0')) : 0;
    const totalDue = consultationFee + bookingPlatformFee;
    const doctorName = selectedDoctor?.dataset.doctorName || 'Hospital appointment';
    const slotLabel = selectedSlotMeta
      ? `${selectedSlotMeta.dateLabel} ${selectedSlotMeta.timeLabel}`
      : 'Pending slot';
    const query = new URLSearchParams({
      pa: hospitalUpiId,
      pn: hospitalUpiPayee,
      am: String(totalDue),
      cu: 'INR',
      tn: `Appointment with Dr. ${doctorName} ${slotLabel}`,
    });
    return {
      totalDue,
      doctorName,
      slotLabel,
      uri: `upi://pay?${query.toString()}`,
    };
  };

  const closeUpiModal = () => {
    if (!upiModal) {
      return;
    }
    upiModal.classList.remove('is-open');
    upiModal.setAttribute('aria-hidden', 'true');
  };

  const openUpiModal = () => {
    if (!upiModal || !hospitalUpiId) {
      showTransientAlert('UPI ID is not configured.', 'error');
      return;
    }
    const paymentData = buildUpiUri();
    if (upiQrImage) {
      upiQrImage.src = `https://quickchart.io/qr?size=320&text=${encodeURIComponent(paymentData.uri)}`;
    }
    if (upiModalLink) {
      upiModalLink.href = paymentData.uri;
    }
    if (upiModalDoctor) {
      upiModalDoctor.textContent = `Dr. ${paymentData.doctorName}`;
    }
    if (upiModalSlot) {
      upiModalSlot.textContent = paymentData.slotLabel;
    }
    if (upiModalTotal) {
      upiModalTotal.textContent = `Rs. ${paymentData.totalDue}`;
    }
    if (upiModalId) {
      upiModalId.textContent = hospitalUpiId;
    }
    upiModal.classList.add('is-open');
    upiModal.setAttribute('aria-hidden', 'false');
  };

  const openUpiCheckoutFromBooking = () => {
    if (paymentField.value !== 'UPI') {
      return false;
    }
    if (allowUpiSubmit) {
      return false;
    }
    if (typeof bookingForm?.reportValidity === 'function' && !bookingForm.reportValidity()) {
      return true;
    }
    if (!doctorField.value || !slotField.value) {
      showTransientAlert('Choose a doctor and slot before opening the payment QR.', 'error');
      return true;
    }
    openUpiModal();
    return true;
  };

  const setSlotSummary = (message, tone = 'default') => {
    if (!slotSummary) {
      return;
    }

    slotSummary.textContent = message;
    slotSummary.classList.toggle('is-error', tone === 'error');
  };

  const setSlotSyncNote = (message) => {
    if (slotSyncNote) {
      slotSyncNote.textContent = message;
    }
  };

  const updateDoctorCardSelection = () => {
    doctorCards.forEach((card) => {
      card.classList.toggle('is-selected', String(card.dataset.doctorId) === String(doctorField.value));
    });
  };

  const updatePaymentOptionSelection = () => {
    paymentOptions.forEach((option) => {
      option.classList.toggle('is-selected', option.dataset.paymentValue === paymentField.value);
    });
  };

  const updateSlotOptionSelection = () => {
    selectedSlotMeta = null;
    Array.from(shell.querySelectorAll('[data-slot-option]')).forEach((option) => {
      const isSelected = String(option.dataset.slotId) === String(slotField.value);
      const radio = option.querySelector('[data-slot-radio]');
      option.classList.toggle('is-selected', isSelected);
      if (radio) {
        radio.checked = isSelected;
      }

      if (isSelected) {
        selectedSlotMeta = {
          id: option.dataset.slotId,
          label: option.dataset.slotLabel,
          dateLabel: option.dataset.slotDateLabel,
          timeLabel: option.dataset.slotTimeLabel,
        };
      }
    });
  };

  const getSlotPeriod = (startTime) => {
    const hour = Number(String(startTime || '00:00').split(':')[0] || '0');
    if (hour < 12) {
      return 'MORNING';
    }
    if (hour < 17) {
      return 'AFTERNOON';
    }
    return 'EVENING';
  };

  const renderSlots = (slots, selectedValue = '') => {
    loadedSlots = slots;
    const visibleSlots = slots.filter((slot) => activeSlotFilter === 'ALL' || getSlotPeriod(slot.start_time) === activeSlotFilter);
    const options = ['<option value="">Select a slot</option>'];

    if (!visibleSlots.length) {
      slotField.innerHTML = options.join('');
      slotField.disabled = true;
      selectedSlotMeta = null;
      if (slotOptions) {
        slotOptions.innerHTML = slots.length
          ? `<div class="booking-empty-state">No ${activeSlotFilter.toLowerCase()} slots are available for this doctor right now.</div>`
          : '<div class="booking-empty-state">No open slots are available for this doctor right now.</div>';
      }
      return;
    }

    const slotMarkup = visibleSlots
      .map((slot) => {
        const isSelected = String(slot.id) === String(selectedValue);
        const selected = isSelected ? ' selected' : '';
        const dateLabel = slot.date_label || slot.date;
        const timeLabel = slot.time_label || `${slot.start_time} - ${slot.end_time}`;

        if (isSelected) {
          selectedSlotMeta = {
            id: String(slot.id),
            label: slot.label,
            dateLabel,
            timeLabel,
          };
        }

        options.push(`<option value="${slot.id}"${selected}>${escapeHtml(slot.label)}</option>`);
        return `
          <label
            class="slot-option${isSelected ? ' is-selected' : ''}"
            data-slot-option
            data-slot-id="${slot.id}"
            data-slot-label="${escapeHtml(slot.label)}"
            data-slot-date-label="${escapeHtml(dateLabel)}"
            data-slot-time-label="${escapeHtml(timeLabel)}"
          >
            <input
              class="slot-option-input"
              type="radio"
              name="interactive-slot-choice"
              value="${slot.id}"
              data-slot-radio
              ${isSelected ? 'checked' : ''}
            >
            <span class="slot-option-marker" aria-hidden="true"></span>
            <span class="slot-option-copy">
              <span class="slot-option-date">${escapeHtml(dateLabel)}</span>
              <strong>${escapeHtml(timeLabel)}</strong>
              <span class="slot-option-meta">Tap to reserve this time</span>
            </span>
          </label>
        `;
      })
      .join('');

    slotField.innerHTML = options.join('');
    slotField.value = visibleSlots.some((slot) => String(slot.id) === String(selectedValue)) ? selectedValue || '' : '';
    slotField.disabled = false;
    if (slotOptions) {
      slotOptions.innerHTML = slotMarkup;
    }
    updateSlotOptionSelection();
  };

  const resetSlots = () => {
    slotRequestId += 1;
    loadedSlots = [];
    slotField.innerHTML = '<option value="">Select a slot</option>';
    slotField.disabled = true;
    selectedSlotMeta = null;
    if (slotOptions) {
      slotOptions.innerHTML = '<div class="booking-empty-state">Choose a doctor to view time slots.</div>';
    }
    setSlotSummary('Choose a doctor to unlock live appointment slots.');
    setSlotSyncNote('Waiting for slot sync');
  };

  const filterDoctorCards = () => {
    if (!doctorCards.length) {
      return;
    }

    const query = (doctorSearch?.value || '').trim().toLowerCase();
    let visibleCount = 0;

    doctorCards.forEach((card) => {
      const matches = !query || (card.dataset.search || '').includes(query);
      card.classList.toggle('is-hidden', !matches);
      if (matches) {
        visibleCount += 1;
      }
    });

    if (doctorSearchCount) {
      doctorSearchCount.textContent = query ? `${visibleCount} shown` : `${doctorCards.length} doctors`;
    }

    if (doctorEmptyState) {
      doctorEmptyState.classList.toggle('is-hidden', visibleCount > 0);
    }
  };

  const updatePreview = () => {
    const selectedDoctor = getSelectedDoctorCard();
    const paymentValue = paymentField.value || '';
    const paymentReady = Boolean(paymentValue);
    const paymentTitle = getPaymentTitle(paymentValue);
    const consultationFee = selectedDoctor ? Math.round(Number(selectedDoctor.dataset.fee || '0')) : 0;
    const totalDue = consultationFee + bookingPlatformFee;
    const gmailValue = gmailField.value.trim();
    const gmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(gmailValue);
    const isReady = Boolean(doctorField.value && slotField.value && paymentReady && gmailValid);
    const doctorText = selectedDoctor ? `Dr. ${selectedDoctor.dataset.doctorName}` : 'Not selected';
    const slotText = selectedSlotMeta
      ? `${selectedSlotMeta.dateLabel} | ${selectedSlotMeta.timeLabel}`
      : 'Not selected';

    if (doctorPreview) {
      doctorPreview.textContent = doctorText;
    }
    if (locationPreview) {
      locationPreview.textContent = selectedDoctor?.dataset.location || 'Waiting for selection';
    }
    if (specializationPreview) {
      specializationPreview.textContent = selectedDoctor?.dataset.specialization || 'Waiting for selection';
    }
    if (experiencePreview) {
      experiencePreview.textContent = selectedDoctor?.dataset.experienceLabel || 'Consultant details pending';
    }
    if (feePreview) {
      feePreview.textContent = selectedDoctor
        ? `Rs. ${consultationFee}`
        : 'Pending selection';
    }
    if (platformFeePreview) {
      platformFeePreview.textContent = `Rs. ${bookingPlatformFee}`;
    }
    if (totalPreview) {
      totalPreview.textContent = `Rs. ${totalDue}`;
    }
    if (nextPreview) {
      nextPreview.textContent = selectedDoctor?.dataset.nextSlot || 'Choose a doctor first';
    }
    if (openSlotsPreview) {
      openSlotsPreview.textContent = selectedDoctor
        ? `${selectedDoctor.dataset.openSlots} available`
        : '0 available';
    }
    if (slotPreview) {
      slotPreview.textContent = slotText;
    }
    if (gmailPreview) {
      gmailPreview.textContent = gmailValue || 'Not provided';
    }
    if (paymentMethodPreview) {
      paymentMethodPreview.textContent = paymentReady ? paymentTitle : 'Not selected';
    }
    if (paymentStatusPreview) {
      paymentStatusPreview.textContent = !paymentReady
        ? 'Awaiting method'
        : paymentValue === 'PAY_AT_HOSPITAL'
          ? 'Pending at hospital desk'
          : 'Will confirm instantly online';
    }
    if (consultationBreakdown) {
      consultationBreakdown.textContent = `Rs. ${consultationFee}`;
    }
    if (platformBreakdown) {
      platformBreakdown.textContent = `Rs. ${bookingPlatformFee}`;
    }
    if (totalBreakdown) {
      totalBreakdown.textContent = `Rs. ${totalDue}`;
    }
    if (readinessPreview) {
      readinessPreview.textContent = isReady
        ? 'Ready to confirm'
        : !doctorField.value
          ? 'Select a doctor'
          : !slotField.value
            ? 'Pick a slot'
            : !paymentReady
              ? 'Choose payment'
            : !gmailValue
              ? 'Enter Email'
              : 'Use a valid Email';
    }
    if (previewNote) {
      previewNote.textContent = isReady
        ? 'Everything is set. Your slot, payment route, and confirmation email are ready for final booking.'
        : !doctorField.value
          ? 'Select a doctor to start building your appointment summary.'
          : !slotField.value
            ? 'Choose one of the live slots to continue.'
            : !paymentReady
              ? 'Choose how you want to pay so we can finalize your booking.'
            : 'Add a valid email address to finish booking.';
    }
    if (paymentFeedback) {
      paymentFeedback.textContent = !paymentReady
        ? 'Select a payment method to continue with secure checkout.'
        : paymentValue === 'UPI'
          ? `Use UPI ID ${hospitalUpiId} to pay Rs. ${totalDue} instantly.`
        : paymentValue === 'PAY_AT_HOSPITAL'
          ? 'Your slot will be reserved now. Payment stays pending until you arrive at the hospital.'
          : `${paymentTitle} will confirm your appointment instantly after booking.`;
      paymentFeedback.classList.toggle('is-success', paymentReady && paymentValue !== 'PAY_AT_HOSPITAL');
      paymentFeedback.classList.toggle('is-error', false);
    }
    if (upiPanel) {
      upiPanel.classList.toggle('is-hidden', paymentValue !== 'UPI');
    }
    if (upiAmount) {
      upiAmount.textContent = `Rs. ${totalDue}`;
    }
    if (upiLink) {
      const query = new URLSearchParams({
        pa: hospitalUpiId,
        pn: hospitalUpiPayee,
        am: String(totalDue),
        cu: 'INR',
        tn: selectedDoctor
          ? `Appointment with Dr. ${selectedDoctor.dataset.doctorName}`
          : 'Hospital appointment booking',
      });
      upiLink.href = `upi://pay?${query.toString()}`;
      upiLink.classList.toggle('is-disabled', !hospitalUpiId);
      upiLink.setAttribute('aria-disabled', hospitalUpiId ? 'false' : 'true');
    }
    if (gmailFeedback) {
      gmailFeedback.textContent = !gmailValue
        ? 'Enter your email address to receive booking confirmation.'
        : gmailValid
          ? 'Perfect! Confirmation will be sent here instantly.'
          : 'Please enter a valid email address.';
      gmailFeedback.classList.toggle('is-error', Boolean(gmailValue) && !gmailValid);
      gmailFeedback.classList.toggle('is-success', gmailValid);
    }
    if (submitButton) {
      submitButton.disabled = !isReady;
      submitButton.textContent = !doctorField.value
        ? 'Select a Doctor First'
        : !slotField.value
          ? 'Choose a Slot'
          : !paymentReady
            ? 'Choose Payment Method'
          : !gmailValid
            ? 'Enter Valid Email'
            : paymentValue === 'PAY_AT_HOSPITAL'
              ? 'Reserve Appointment'
              : paymentValue === 'UPI'
                ? 'Open QR and Pay'
                : 'Continue to Payment';
    }

    const states = [Boolean(doctorField.value), Boolean(slotField.value), paymentReady, gmailValid];
    steps.forEach((step, index) => {
      const isComplete = states[index];
      const isCurrent = !isComplete && (index === 0 ? true : states.slice(0, index).every(Boolean));
      step.classList.toggle('is-complete', isComplete);
      step.classList.toggle('is-current', isCurrent);
      step.classList.toggle('is-active', isComplete || isCurrent);
    });

    updateDoctorCardSelection();
    updateSlotOptionSelection();
    updatePaymentOptionSelection();
  };

  const loadSlots = async (preserveSelection = false) => {
    if (!doctorField.value || !slotsUrlTemplate) {
      resetSlots();
      updatePreview();
      return;
    }

    const requestId = slotRequestId + 1;
    slotRequestId = requestId;
    const selectedDoctor = getSelectedDoctorCard();
    const currentValue = preserveSelection ? slotField.value : '';
    if (!preserveSelection) {
      slotField.value = '';
      selectedSlotMeta = null;
    }

    slotField.disabled = true;
    slotField.innerHTML = '<option value="">Loading slots...</option>';
    if (slotOptions) {
      slotOptions.innerHTML = '<div class="booking-empty-state is-loading">Loading available slots...</div>';
    }
    setSlotSummary(
      selectedDoctor
        ? `Checking open slots for Dr. ${selectedDoctor.dataset.doctorName}...`
        : 'Checking available slots...'
    );

    try {
      const url = slotsUrlTemplate.replace('/0/', `/${doctorField.value}/`);
      const data = await requestJSON(url);
      if (requestId !== slotRequestId) {
        return;
      }
      renderSlots(data.slots || [], currentValue);
      setSlotSyncNote(`Last refreshed at ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
      setSlotSummary(
        (data.slots || []).length
          ? `${data.slots.length} live slot${data.slots.length === 1 ? '' : 's'} available for Dr. ${selectedDoctor?.dataset.doctorName || 'this doctor'}.`
          : `No open slots available for Dr. ${selectedDoctor?.dataset.doctorName || 'this doctor'} right now.`,
        (data.slots || []).length ? 'default' : 'error'
      );
    } catch (error) {
      if (requestId !== slotRequestId) {
        return;
      }
      slotField.innerHTML = '<option value="">Unable to load slots</option>';
      slotField.disabled = true;
      selectedSlotMeta = null;
      if (slotOptions) {
        slotOptions.innerHTML = '<div class="booking-empty-state">Unable to load slots right now. Please try again.</div>';
      }
      setSlotSummary('Unable to load available slots right now.', 'error');
      setSlotSyncNote('Sync failed');
      showTransientAlert('Unable to load available slots right now.', 'error');
    }

    updatePreview();
  };

  doctorCards.forEach((card) => {
    card.addEventListener('click', () => {
      const nextDoctorId = card.dataset.doctorId || '';
      const doctorChanged = String(doctorField.value) !== String(nextDoctorId);
      doctorField.value = nextDoctorId;

      if (doctorChanged) {
        loadSlots(false);
      } else {
        updatePreview();
      }
    });
  });

  paymentOptions.forEach((option) => {
    option.addEventListener('click', () => {
      paymentField.value = option.dataset.paymentValue || '';
      updatePaymentOptionSelection();
      updatePreview();
    });
  });

  showUpiQrButton?.addEventListener('click', () => {
    if (paymentField.value === 'UPI') {
      openUpiModal();
    }
  });

  upiIdTrigger?.addEventListener('click', () => {
    if (paymentField.value === 'UPI') {
      openUpiModal();
    }
  });

  copyUpiButton?.addEventListener('click', async () => {
    if (!hospitalUpiId) {
      showTransientAlert('UPI ID is not configured.', 'error');
      return;
    }

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(hospitalUpiId);
      }
      showTransientAlert(`UPI ID copied: ${hospitalUpiId}`);
    } catch (error) {
      showTransientAlert(`Copy this UPI ID manually: ${hospitalUpiId}`, 'error');
    }
  });

  upiCloseButtons.forEach((button) => {
    button.addEventListener('click', closeUpiModal);
  });

  upiModal?.addEventListener('click', (event) => {
    if (event.target === upiModal) {
      closeUpiModal();
    }
  });

  upiConfirmButton?.addEventListener('click', () => {
    allowUpiSubmit = true;
    closeUpiModal();
    if (bookingForm?.requestSubmit) {
      bookingForm.requestSubmit();
      return;
    }
    bookingForm?.submit();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeUpiModal();
    }
  });

  slotFilterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      activeSlotFilter = button.dataset.slotFilter || 'ALL';
      slotFilterButtons.forEach((item) => item.classList.remove('is-active'));
      button.classList.add('is-active');
      if (!doctorField.value) {
        resetSlots();
        return;
      }
      renderSlots(loadedSlots, slotField.value);
      updatePreview();
    });
  });

  doctorSearch?.addEventListener('input', filterDoctorCards);
  slotOptions?.addEventListener('change', (event) => {
    const radio = event.target.closest('[data-slot-radio]');
    if (!radio) {
      return;
    }

    slotField.value = radio.value || '';
    updateSlotOptionSelection();
    updatePreview();
  });
  slotOptions?.addEventListener('click', (event) => {
    const option = event.target.closest('[data-slot-option]');
    if (!option) {
      return;
    }

    const radio = option.querySelector('[data-slot-radio]');
    if (radio) {
      radio.checked = true;
    }
    slotField.value = option.dataset.slotId || '';
    updateSlotOptionSelection();
    updatePreview();
  });

  doctorField.addEventListener('change', () => loadSlots(false));
  slotField.addEventListener('change', () => {
    updateSlotOptionSelection();
    updatePreview();
  });
  paymentField.addEventListener('change', updatePreview);
  gmailField.addEventListener('input', updatePreview);
  submitButton?.addEventListener('click', (event) => {
    if (openUpiCheckoutFromBooking()) {
      event.preventDefault();
    }
  });
  bookingForm?.addEventListener('submit', (event) => {
    if (paymentField.value !== 'UPI') {
      return;
    }
    if (allowUpiSubmit) {
      allowUpiSubmit = false;
      return;
    }
    event.preventDefault();
    openUpiCheckoutFromBooking();
  });

  filterDoctorCards();
  updateDoctorCardSelection();
  updatePaymentOptionSelection();
  if (doctorField.value) {
    loadSlots(true);
  } else {
    resetSlots();
    updatePreview();
  }

  window.setInterval(() => {
    if (document.visibilityState === 'visible' && doctorField.value) {
      loadSlots(true);
    }
  }, 15000);
}

function initAdminChart() {
  const shell = document.querySelector('[data-admin-chart]');
  const canvas = document.getElementById('revenueChart');
  if (!shell || !canvas || typeof Chart === 'undefined') {
    return;
  }

  const chart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: ['Revenue'],
      datasets: [
        {
          label: 'Amount',
          data: [Number(shell.dataset.revenue || '0')],
          backgroundColor: ['#0f766e'],
          borderRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: true,
        },
      },
    },
  });

  shell._chart = chart;
  shell._chartView = 'revenue';

  shell.querySelectorAll('[data-chart-view]').forEach((button) => {
    button.addEventListener('click', () => {
      shell.querySelectorAll('[data-chart-view]').forEach((item) => item.classList.remove('is-active'));
      button.classList.add('is-active');
      shell._chartView = button.dataset.chartView || 'revenue';
      refreshAdminChart(shell);
    });
  });

  refreshAdminChart(shell);
}

function initLiveDashboardStats() {
  const body = document.body;
  const statsUrl = body.dataset.dashboardStatsUrl;
  const liveShell = document.querySelector('[data-live-dashboard]');

  if (!statsUrl || !liveShell) {
    return;
  }

  const refreshStats = async () => {
    try {
      const stats = await requestJSON(statsUrl);
      liveShell.querySelectorAll('[data-stat-key]').forEach((element) => {
        const key = element.dataset.statKey;
        if (key in stats) {
          setMetricValue(element, stats[key]);
        }
      });

      const adminChartShell = document.querySelector('[data-admin-chart]');
      if (adminChartShell && stats.role === 'ADMIN') {
        adminChartShell.dataset.revenue = Math.round(Number(stats.revenue_sum || 0));
        adminChartShell.dataset.booked = stats.booked_count || 0;
        adminChartShell.dataset.completed = stats.completed_count || 0;
        adminChartShell.dataset.cancelled = stats.cancelled_count || 0;
        refreshAdminChart(adminChartShell);
      }
    } catch (error) {
      // Silent retry for polling.
    }
  };

  refreshStats();
  window.setInterval(refreshStats, 15000);
}

function initLiveNotifications() {
  const body = document.body;
  const notificationsUrl = body.dataset.notificationsApi;
  const readAllUrl = body.dataset.notificationsReadAllUrl;
  const readUrlTemplate = body.dataset.notificationReadUrlTemplate || '';
  const badge = document.querySelector('[data-notification-count]');
  const panel = document.querySelector('[data-notification-panel]');

  if (!notificationsUrl) {
    return;
  }

  const refreshNotifications = async () => {
    try {
      const data = await requestJSON(notificationsUrl);
      updateNotificationBadge(badge, data.unread_count || 0);

      if (panel) {
        renderNotificationList(panel, data.notifications || [], readUrlTemplate);
      }
    } catch (error) {
      // Silent retry for polling.
    }
  };

  if (panel) {
    panel.addEventListener('click', async (event) => {
      const readButton = event.target.closest('[data-notification-read]');
      const readAllButton = event.target.closest('[data-notification-read-all]');

      if (readButton) {
        setButtonLoading(readButton, true);
        try {
          await requestJSON(readButton.dataset.notificationRead, {
            method: 'POST',
          });
          await refreshNotifications();
        } catch (error) {
          showTransientAlert('Unable to mark that notification as read.', 'error');
        } finally {
          setButtonLoading(readButton, false);
        }
      }

      if (readAllButton && readAllUrl) {
        setButtonLoading(readAllButton, true);
        try {
          await requestJSON(readAllUrl, {
            method: 'POST',
          });
          await refreshNotifications();
        } catch (error) {
          showTransientAlert('Unable to mark all notifications as read.', 'error');
        } finally {
          setButtonLoading(readAllButton, false);
        }
      }
    });
  }

  refreshNotifications();
  window.setInterval(refreshNotifications, 12000);
}

function initAppointmentActions() {
  document.querySelectorAll('[data-status-action]').forEach((button) => {
    button.addEventListener('click', async () => {
      const row = button.closest('tr');
      const badge = row?.querySelector('.badge');

      setButtonLoading(button, true);
      try {
        const data = await requestJSON(button.dataset.url, {
          method: 'POST',
        });

        if (row) {
          row.dataset.status = data.status || button.dataset.nextStatus || 'BOOKED';
          row.dataset.rowSearch = `${row.dataset.rowSearch || ''} ${data.status_label || ''}`.trim();
        }

        if (badge) {
          badge.textContent = data.status || button.dataset.nextStatus || 'BOOKED';
          badge.className = `badge ${badgeClassForStatus(data.status || button.dataset.nextStatus || 'BOOKED')}`;
        }

        showTransientAlert(`Appointment updated to ${data.status_label || data.status}.`);
      } catch (error) {
        showTransientAlert('Unable to update the appointment right now.', 'error');
      } finally {
        setButtonLoading(button, false);
      }
    });
  });
}

function refreshAdminChart(shell) {
  if (!shell || !shell._chart) {
    return;
  }

  const chart = shell._chart;
  const currentView = shell._chartView || 'revenue';
  const revenueValue = Number(shell.dataset.revenue || '0');
  const bookedValue = Number(shell.dataset.booked || '0');
  const completedValue = Number(shell.dataset.completed || '0');
  const cancelledValue = Number(shell.dataset.cancelled || '0');

  if (currentView === 'status') {
    chart.config.type = 'doughnut';
    chart.data.labels = ['Booked', 'Completed', 'Cancelled'];
    chart.data.datasets = [
      {
        label: 'Appointments',
        data: [bookedValue, completedValue, cancelledValue],
        backgroundColor: ['#3b82f6', '#16a34a', '#ef4444'],
        borderWidth: 0,
      },
    ];
  } else {
    chart.config.type = 'bar';
    chart.data.labels = ['Revenue'];
    chart.data.datasets = [
      {
        label: 'Amount',
        data: [revenueValue],
        backgroundColor: ['#0f766e'],
        borderRadius: 10,
      },
    ];
  }

  chart.update();
}

function scrollChatsToBottom() {
  document.querySelectorAll('.chat-box').forEach((box) => {
    box.scrollTop = box.scrollHeight;
  });
}

function appendChatMessage(container, text, isStaff) {
  const message = document.createElement('div');
  message.className = isStaff ? 'chat-message staff' : 'chat-message';
  message.textContent = text;
  container.appendChild(message);
}

function animateMetricValue(element, target) {
  const safeTarget = Number(target || 0);
  const prefix = element.dataset.prefix || '';
  const start = 0;
  const duration = 700;
  const begin = performance.now();

  function step(timestamp) {
    const progress = Math.min((timestamp - begin) / duration, 1);
    const value = Math.round(start + (safeTarget - start) * easeOutCubic(progress));
    element.textContent = `${prefix}${value}`;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      element.textContent = `${prefix}${Math.round(safeTarget)}`;
    }
  }

  window.requestAnimationFrame(step);
}

function setMetricValue(element, value) {
  const prefix = element.dataset.prefix || '';
  const nextValue = Math.round(Number(value || 0));
  const currentValue = Number((element.textContent || '').replace(/[^\d.-]/g, '')) || 0;

  if (currentValue === nextValue) {
    return;
  }

  element.classList.add('is-updating');
  element.dataset.count = String(nextValue);
  element.textContent = `${prefix}${nextValue}`;
  window.setTimeout(() => element.classList.remove('is-updating'), 500);
}

function updateNotificationBadge(badge, count) {
  if (!badge) {
    return;
  }

  const safeCount = Number(count || 0);
  badge.textContent = safeCount;
  badge.classList.toggle('is-hidden', safeCount <= 0);
}

function renderNotificationList(panel, notifications, readUrlTemplate) {
  const list = panel.querySelector('[data-notification-list]');
  if (!list) {
    return;
  }

  if (!notifications.length) {
    list.innerHTML = '<div class="notification-empty" data-notification-empty>No notifications</div>';
    return;
  }

  list.innerHTML = notifications
    .map((item) => {
      const action = item.is_read
        ? ''
        : `<button type="button" class="btn btn-outline notification-action" data-notification-read="${escapeHtml(readUrlTemplate.replace('/0/', `/${item.id}/`))}">Mark Read</button>`;

      return `
        <div class="notification-item ${item.is_read ? 'is-read' : ''}" data-notification-id="${item.id}">
          <div>
            <strong>${escapeHtml(item.message)}</strong>
            <div class="summary-hint">${escapeHtml(item.created_at)}</div>
          </div>
          ${action}
        </div>
      `;
    })
    .join('');
}

function setButtonLoading(button, isLoading) {
  if (!button) {
    return;
  }

  button.classList.toggle('is-loading', isLoading);
  button.disabled = isLoading;
}

async function requestJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': getCsrfToken(),
      ...(options.headers || {}),
    },
    credentials: 'same-origin',
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

function getCsrfToken() {
  const name = 'csrftoken=';
  const cookies = document.cookie.split(';');
  for (let index = 0; index < cookies.length; index += 1) {
    const cookie = cookies[index].trim();
    if (cookie.startsWith(name)) {
      return decodeURIComponent(cookie.slice(name.length));
    }
  }
  return '';
}

function badgeClassForStatus(status) {
  if (status === 'COMPLETED') {
    return 'badge-completed';
  }
  if (status === 'CANCELLED') {
    return 'badge-cancelled';
  }
  return 'badge-booked';
}

function showTransientAlert(message, tone = 'success') {
  const pageShell = document.querySelector('.page-shell');
  if (!pageShell) {
    return;
  }

  const alert = document.createElement('div');
  alert.className = 'alert';
  if (tone === 'error') {
    alert.style.borderColor = '#fecaca';
    alert.style.color = '#991b1b';
    alert.style.background = 'linear-gradient(180deg, #fff1f2, #fff7ed)';
  }
  alert.setAttribute('data-alert', 'true');
  alert.innerHTML = `
    <span>${escapeHtml(message)}</span>
    <button type="button" class="alert-close" aria-label="Dismiss message" data-alert-close>&times;</button>
  `;

  pageShell.prepend(alert);
  const closeButton = alert.querySelector('[data-alert-close]');
  if (closeButton) {
    closeButton.addEventListener('click', () => hideAlert(alert));
  }

  window.setTimeout(() => hideAlert(alert), 3500);
}

function hideAlert(alert) {
  if (!alert) {
    return;
  }
  alert.classList.add('is-hiding');
  window.setTimeout(() => alert.remove(), 220);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function easeOutCubic(value) {
  return 1 - Math.pow(1 - value, 3);
}
